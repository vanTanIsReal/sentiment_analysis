"""Worker xử lý đánh giá mới — Few-shot LLM → JSON (aspect + sentiment)."""

from __future__ import annotations

import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from sqlalchemy import delete

REPO_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(REPO_ROOT / ".env")
os.chdir(REPO_ROOT)

from ai_worker.backend_path import ensure_backend_on_path
from ai_worker.services.analyzer import analyze_review_text

ensure_backend_on_path()

from app.db.database import SessionLocal  # noqa: E402
from app.models import AspectSentiment, Review  # noqa: E402

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="NLP — AI Worker", version="0.1.0")


@app.post("/analyze/{review_id}")
def analyze_review(review_id: int) -> dict:
    db = SessionLocal()
    try:
        rev = db.get(Review, review_id)
        if not rev:
            raise HTTPException(status_code=404, detail="Không tìm thấy review")

        rev.analysis_status = "pending"
        db.commit()

        try:
            rows = analyze_review_text(rev.content)
        except Exception as e:
            logger.exception("Phân tích LLM thất bại")
            rev.analysis_status = "error"
            db.commit()
            raise HTTPException(status_code=502, detail=str(e)) from e

        db.execute(delete(AspectSentiment).where(AspectSentiment.review_id == rev.id))
        for r in rows:
            db.add(
                AspectSentiment(
                    review_id=rev.id,
                    aspect=r["aspect"],
                    sentiment=r["sentiment"],
                    confidence=r.get("confidence"),
                    quote=r.get("quote"),
                )
            )
        rev.analysis_status = "done"
        db.commit()
        return {"review_id": rev.id, "aspects": len(rows), "status": rev.analysis_status}
    finally:
        db.close()


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "ai_worker"}
