"""Cấu hình ứng dụng từ biến môi trường."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_REPO = Path(__file__).resolve().parents[3]
_ENV_CANDIDATES = [_REPO / ".env", Path(".env")]


def _pick_env_file() -> str | Path:
    for p in _ENV_CANDIDATES:
        if isinstance(p, Path) and p.is_file():
            return p
    return ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_pick_env_file(),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "sqlite:///./data/app.db"
    backend_host: str = "127.0.0.1"
    backend_port: int = 8000
    ai_worker_url: str = "http://127.0.0.1:8001"
    data_dir: str = "./data"
    cors_origins: str = "*"  # hoặc danh sách CSV, ví dụ: http://localhost:3000,http://127.0.0.1:3000


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
