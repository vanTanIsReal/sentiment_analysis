"""Nạp dữ liệu mẫu / crawl vào database."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import func, select

REPO = Path(__file__).resolve().parents[1]
load_dotenv(REPO / ".env")
sys.path.insert(0, str(REPO / "backend"))

import app.models  # noqa: E402, F401 — đăng ký bảng ORM
from app.db.database import Base, SessionLocal, engine  # noqa: E402
from app.models import Product, Review  # noqa: E402


def seed(jsonl: Path | None = None) -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.scalar(select(Product).limit(1)):
            print("Database already has data - skipping seed (delete DB to re-seed).")
            return

        p = Product(
            name="iPhone (ví dụ)",
            brand="Apple",
            url="https://www.thegioididong.com/example-product",
            price=19_990_000,
            external_id="demo-iphone",
        )
        db.add(p)
        db.commit()
        db.refresh(p)

        rows: list[dict] = []
        if jsonl and jsonl.is_file():
            for line in jsonl.open(encoding="utf-8"):
                line = line.strip()
                if line:
                    rows.append(json.loads(line))

        if not rows:
            rows = [
                {
                    "text": "Màn hình đẹp, pin trâu, chơi game mượt. Giá hơi cao.",
                    "rating": 5,
                    "author": "demo_user",
                },
                {
                    "text": "Camera chụp tạm được, loa hơi nhỏ.",
                    "rating": 4,
                    "author": "user2",
                },
            ]

        for r in rows[:500]:
            db.add(
                Review(
                    product_id=p.id,
                    content=str(r.get("text", "")),
                    rating=r.get("rating"),
                    author=r.get("author"),
                    source="seed",
                    analysis_status="pending",
                )
            )

        db.commit()
        n_rev = db.scalar(select(func.count()).select_from(Review).where(Review.product_id == p.id)) or 0
        print(f"Seeded 1 product and {int(n_rev)} reviews.")
    finally:
        db.close()


if __name__ == "__main__":
    jl = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO / "data" / "raw" / "tgdd" / "crawl_snapshot.jsonl"
    seed(jl if jl.exists() else None)
