from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent
if not (BASE_DIR / ".env").exists():
    BASE_DIR = BASE_DIR.parent

ENV_FILE_PATH = BASE_DIR / ".env"

class Settings(BaseSettings):
    DATABASE_URL: str = "mysql+pymysql://root:123456@localhost:3306/research_db"
    SECRET_KEY: str = "super_secret_key_research_project_2026"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE_PATH),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()