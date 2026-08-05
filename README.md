# HACKSPIRE: LUMINA — Backend API

FastAPI backend for the HACKSPIRE: LUMINA hackathon platform. Backend only — the
deliverable is the API plus its auto-generated Swagger documentation.

## Run locally

```bash
# 1. (once) create a venv and install dependencies
python -m venv venv
venv\Scripts\pip install -r requirements.txt

# 2. run the server
venv\Scripts\uvicorn app.main:app --reload
```

- **Swagger UI**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc
- Base path for all endpoints: `/api/v1`

## Configuration

Copy `.env.example` to `.env` and adjust. Key settings:

| Variable | Default | Notes |
| --- | --- | --- |
| `DATABASE_URL` | *(unset)* | Supabase Postgres URL in production. If unset, the app falls back to a local SQLite file `./hackspire.db` — no external service needed. `postgresql://` URLs are automatically upgraded to `postgresql+asyncpg://`. |
| `JWT_SECRET` | `change-me-in-production` | HS256 signing secret. |
| `ADMIN_EMAIL` / `ADMIN_PASSWORD` | `admin@hackspire.dev` / `admin123` | A bootstrap admin account is created on startup if no admin exists. |
| `UPLOAD_DIR` | `./uploads` | Local disk storage for materials, behind an interface swappable for Supabase Storage. |

Tables are created automatically on startup (`create_all`) — no migration step.

## Auth flow

1. `POST /api/v1/auth/login` with `{username, password}` — username is the email
   **or** student/staff ID. Returns `{jwt, first_login}`.
2. If `first_login` is `true`, the account must call
   `POST /api/v1/auth/change-password` before any other endpoint (everything else
   returns 403 until then), then log in again.
3. Send `Authorization: Bearer <jwt>` on every request. Guard levels:
   participant (any logged-in user), team leader (leader of the team in the
   path) and admin.

Participants are provisioned by an admin via the two-step Excel import
(`POST /api/v1/admin/participants/import` to preview, then `/import/confirm` to
create accounts). The expected sheet header is `name, email, student_staff_id`;
the initial password is the student/staff ID.

All error responses share the shape `{"error": "<message>"}`.
