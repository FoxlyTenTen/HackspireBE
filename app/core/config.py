from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    database_url: str = "sqlite+aiosqlite:///./hackspire.db"

    # Supabase Auth — the only authentication mechanism. All values come from
    # the Supabase dashboard (Settings → API). jwt_secret is only needed for
    # legacy HS256 projects; newer projects use asymmetric keys and are
    # verified via the project's JWKS endpoint automatically.
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""
    supabase_jwt_secret: str = ""

    # Where Supabase's invite / password-reset / email-change links land.
    frontend_url: str = "http://localhost:5173"

    admin_email: str = "admin@hackspire.dev"
    admin_password: str = "admin123"
    admin_name: str = "HACKSPIRE Admin"
    admin_student_staff_id: str = "ADMIN-001"

    upload_dir: str = "./uploads"
    participant_cap: int = 400

    # Supabase Storage buckets (public) — must already exist in the project.
    supabase_storage_bucket_materials: str = "materials"
    supabase_storage_bucket_announcements: str = "announcement-images"

    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    # Brevo Transactional API — an alternative to Supabase's own
    # SMTP-triggered mailer for auth emails (invite / reset / email-change).
    # Supabase's own mailer keeps working unchanged unless
    # use_brevo_transactional_email is explicitly turned on; flipping it back
    # off instantly reverts to that default path with no redeploy of code.
    # `validation_alias="SMTP_API"` matches the .env var name already set up
    # for this — the Brevo Transactional API key, NOT the SMTP key used in
    # Supabase's own SMTP settings (those are two different Brevo keys).
    brevo_api_key: str = Field(default="", validation_alias="SMTP_API")
    brevo_invite_template_id: int | None = None
    use_brevo_transactional_email: bool = False

    # Public landing-page "Help Desk" contact form (POST /public/contact) —
    # sent via the same Brevo Transactional API key as above, but as a plain
    # email (no template), since this one has no fixed Brevo template. The
    # sender must be a domain/address verified in Brevo (Senders & IP), or
    # Brevo rejects the send.
    brevo_sender_email: str = "noreply@hackspirelumina.com"
    brevo_sender_name: str = "Hackspire: Lumina"
    contact_recipient_email: str = "hackspirelumina@gmail.com"

    @property
    def sqlalchemy_database_url(self) -> str:
        url = self.database_url
        if url.startswith("postgres://"):
            url = "postgresql+asyncpg://" + url[len("postgres://"):]
        elif url.startswith("postgresql://"):
            url = "postgresql+asyncpg://" + url[len("postgresql://"):]
        return url


# Static event content served by GET /event/info (countdown + timeline come
# from the database; the rest has no table in the schema by design).
EVENT_INFO = {
    "name": "HACKSPIRE: LUMINA",
    "tagline": "Illuminate your ideas. Build the future in 24 hours.",
    "venue": "Multipurpose Hall, Main Campus",
    "sponsors": [
        {"name": "Lumina Labs", "tier": "platinum"},
        {"name": "Spire Cloud", "tier": "gold"},
        {"name": "Nova Devtools", "tier": "silver"},
    ],
    "prize_pool": {
        "total": "RM 10,000",
        "breakdown": [
            {"placement": "champion", "prize": "RM 5,000"},
            {"placement": "1st runner-up", "prize": "RM 3,000"},
            {"placement": "2nd runner-up", "prize": "RM 2,000"},
        ],
    },
    "contact": {
        "email": "hackspire@lumina.dev",
        "phone": "+60 12-345 6789",
        "instagram": "@hackspire.lumina",
    },
}


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
