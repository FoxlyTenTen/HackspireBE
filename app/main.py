from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings
from app.core.errors import ApiError
from app.core.limiter import limiter
from app.db.base import Base
from app.db.models import AuditLog, EventSettings  # noqa: F401 — ensure models are registered
from app.db.session import async_session_factory, engine
from app.routers import (
    admin_content,
    admin_participants,
    admin_submissions,
    admin_teams,
    auth,
    content,
    join_requests,
    notifications,
    participants,
    profile,
    public,
    submissions,
    teams,
)
from app.services.auth import seed_admin
from app.services.submissions import get_event_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with async_session_factory() as session:
        await seed_admin(session)
        await get_event_settings(session)
        await session.commit()
    yield
    await engine.dispose()


app = FastAPI(
    title="HACKSPIRE: LUMINA API",
    description=(
        "Backend API for the HACKSPIRE: LUMINA hackathon platform.\n\n"
        "Participants log in with pre-provisioned accounts (imported from Excel by "
        "an admin), form teams of up to 5, request to join teams, and submit a "
        "GitHub or Google Drive project link before the deadline. Admins approve "
        "or reject teams (approval locks the team), manage event content "
        "(countdown, timeline, materials, announcements, finalists, winners) and "
        "export submissions for judging.\n\n"
        "**Auth**: every route except `POST /api/v1/auth/login` requires an "
        "`Authorization: Bearer <jwt>` header. Accounts flagged `first_login` must "
        "call `/auth/change-password` before anything else. All errors use the "
        'shape `{"error": "<message>"}`.'
    ),
    version="0.1.0",
    lifespan=lifespan,
)
# In-memory, per-instance rate limiting on auth endpoints (see
# app/routers/auth.py). Cloud Run can run multiple instances, so this is
# best-effort per-instance protection against brute-force/credential
# stuffing, not a hard global cap — acceptable for basic hardening at this
# scale without adding a Redis dependency.
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


assert "*" not in settings.cors_origins, (
    "CORS_ORIGINS must not contain '*' when allow_credentials=True"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    """A handful of standard response headers — no CSP here since this is a
    pure JSON API, not HTML; CSP belongs on the frontend's Nginx layer
    instead. Strict-Transport-Security is safe to always send since Cloud
    Run enforces HTTPS for every deployed URL (no plain-HTTP path exists)."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
    return response


@app.get("/", include_in_schema=False)
def root():
    return {"status": "ok"}


@app.exception_handler(ApiError)
async def api_error_handler(request: Request, exc: ApiError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"error": exc.message})


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"error": str(exc.detail)})


@app.exception_handler(RequestValidationError)
async def validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    first = exc.errors()[0] if exc.errors() else {}
    location = ".".join(str(part) for part in first.get("loc", []))
    message = first.get("msg", "Invalid request")
    return JSONResponse(status_code=422, content={"error": f"{location}: {message}"})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    # Catch-all so an unexpected bug never surfaces a framework-default body
    # (stack trace, internals) to the client — logs still get the real
    # exception via FastAPI's default logging of unhandled errors.
    return JSONResponse(status_code=500, content={"error": "Internal server error"})


API_PREFIX = "/api/v1"

app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(public.router, prefix=API_PREFIX)
app.include_router(content.router, prefix=API_PREFIX)
app.include_router(participants.router, prefix=API_PREFIX)
app.include_router(profile.router, prefix=API_PREFIX)
app.include_router(teams.router, prefix=API_PREFIX)
app.include_router(join_requests.router, prefix=API_PREFIX)
app.include_router(notifications.router, prefix=API_PREFIX)
app.include_router(submissions.router, prefix=API_PREFIX)
app.include_router(admin_participants.router, prefix=API_PREFIX)
app.include_router(admin_teams.router, prefix=API_PREFIX)
app.include_router(admin_content.router, prefix=API_PREFIX)
app.include_router(admin_submissions.router, prefix=API_PREFIX)
