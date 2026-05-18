"""FastAPI entrypoint — Phần 2: Backend Server."""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import admin, products, reviews
from app.core.config import settings
from app.db.database import Base, engine
import app.models  # noqa: F401 — đăng ký metadata ORM
from app.schemas import HealthResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs(settings.data_dir, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    yield


def _parse_cors(origins: str) -> list[str]:
    o = origins.strip()
    if o == "*":
        return ["*"]
    return [x.strip() for x in o.split(",") if x.strip()]


app = FastAPI(
    title="NLP — Backend TGDD",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_parse_cors(settings.cors_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(products.router, prefix="/api")
app.include_router(reviews.router, prefix="/api")
app.include_router(admin.router, prefix="/api")


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse()
