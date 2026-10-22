"""Application configuration loaded from environment variables."""
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Anchor the default SQLite file to the backend directory so the DB is the same
# regardless of the current working directory (API server vs. the news script).
_BACKEND_DIR = Path(__file__).resolve().parent.parent
_DEFAULT_DB = f"sqlite:///{(_BACKEND_DIR / 'visaroo.db').as_posix()}"


class Settings(BaseSettings):
    """Central settings object. Values come from the environment / .env file."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    secret_key: str = "dev-insecure-secret-change-me"
    access_token_expire_minutes: int = 60 * 24 * 7
    database_url: str = _DEFAULT_DB
    algorithm: str = "HS256"

    # AI
    ai_provider: str = "local"  # "local" | "bedrock"
    aws_region: str = "us-east-1"
    bedrock_text_model_id: str = "anthropic.claude-3-haiku-20240307-v1:0"
    bedrock_embed_model_id: str = "amazon.titan-embed-text-v2:0"
    # Optional Knowledge Base for creator-feed source matching; empty = use local matcher.
    bedrock_knowledge_base_id: str = ""

    # Crypto (encryption at rest for sensitive profile fields)
    crypto_provider: str = "local"  # "local" (Fernet) | "kms" (AWS KMS)
    kms_key_id: str = ""            # KMS key id/ARN/alias, required when crypto_provider=kms
    # Base64 Fernet key for the local provider. If empty, a dev key is derived from
    # secret_key so the app runs out of the box (set this in production).
    fernet_key: str = ""

    # Email (deadline reminders)
    email_provider: str = "local"  # "local" (log preview) | "ses" (Amazon SES)
    ses_from_email: str = ""        # verified SES identity, required when email_provider=ses

    # CORS
    frontend_origin: str = "http://localhost:5173"


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()


# Canonical visa categories reused across the app.
VISA_CATEGORIES = [
    "F-1",
    "OPT",
    "STEM-OPT",
    "H-1B",
    "H-4",
    "J-1",
    "L-1",
    "Green-Card",
    "Other",
]
