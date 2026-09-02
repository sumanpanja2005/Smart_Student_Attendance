from pathlib import Path
from typing import Optional, List
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE = BACKEND_DIR / ".env"


class Settings(BaseSettings):
    # Environment & Deployment Mode
    ENVIRONMENT: str = "development"  # "development" or "production"
    MONGODB_URI: Optional[str] = None
    MONGODB_DATABASE: str = "smart_attendance"
    FRONTEND_URL: str = "http://localhost:5173"
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

    # JWT Authentication
    JWT_SECRET_KEY: Optional[str] = None
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Rate Limiting & Abuse Protection
    RATE_LIMIT_LOGIN_PER_MINUTE: int = 10
    RATE_LIMIT_FACE_PER_MINUTE: int = 20
    RATE_LIMIT_REPORT_PER_MINUTE: int = 10

    # File Storage & Retention
    REPORTS_DIR: str = str(BACKEND_DIR / "app" / "reports_storage")
    AUDIT_LOG_RETENTION_DAYS: int = 365

    # Face Recognition Parameters (Configurable thresholds)
    FACE_MATCH_THRESHOLD: float = 0.50
    FACE_MIN_DETECTION_CONFIDENCE: float = 0.50
    FACE_MIN_SIZE_PX: int = 80
    FACE_BLUR_THRESHOLD: float = 25.0
    FACE_BRIGHTNESS_MIN: float = 10.0
    FACE_BRIGHTNESS_MAX: float = 240.0
    FACE_MAX_UPLOAD_SIZE_MB: int = 5

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE) if ENV_FILE.exists() else None,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @model_validator(mode="after")
    def validate_jwt_secret(self):
        if not self.JWT_SECRET_KEY or not self.JWT_SECRET_KEY.strip():
            raise ValueError(
                "CRITICAL SECURITY CONFIGURATION ERROR: 'JWT_SECRET_KEY' environment variable is missing or empty. "
                "You must specify a secure JWT_SECRET_KEY in backend/.env or environment variables."
            )
        return self

    def get_cors_origins_list(self) -> List[str]:
        origins = [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]
        if self.FRONTEND_URL and self.FRONTEND_URL not in origins:
            origins.append(self.FRONTEND_URL.strip())
        return list(set(origins))


settings = Settings()
