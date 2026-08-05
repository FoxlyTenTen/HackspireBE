from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    database_url: str = "sqlite+aiosqlite:///./hackspire.db"

    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expires_min: int = 60 * 24

    admin_email: str = "admin@hackspire.dev"
    admin_password: str = "admin123"
    admin_name: str = "HACKSPIRE Admin"
    admin_student_staff_id: str = "ADMIN-001"

    upload_dir: str = "./uploads"
    participant_cap: int = 150

    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

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
