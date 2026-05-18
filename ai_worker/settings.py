"""Cấu hình AI Worker."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_REPO = Path(__file__).resolve().parents[1]
_ENV_CANDIDATES = [_REPO / ".env", Path(".env")]


def _pick_env_file() -> str | Path:
    for p in _ENV_CANDIDATES:
        if isinstance(p, Path) and p.is_file():
            return p
    return ".env"


class WorkerSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_pick_env_file(),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "sqlite:///./data/app.db"
    openai_api_key: str | None = None
    gemini_api_key: str | None = None
    llm_provider: str = Field(default="gemini", description="gemini or openai")
    ai_worker_host: str = "127.0.0.1"
    ai_worker_port: int = 8001
    llm_model_openai: str = "gpt-4o-mini"
    llm_model_gemini: str = "gemini-1.5-flash"


@lru_cache
def get_worker_settings() -> WorkerSettings:
    return WorkerSettings()


settings = get_worker_settings()
