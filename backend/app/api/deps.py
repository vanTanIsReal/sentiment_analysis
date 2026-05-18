"""Phụ thuộc dùng chung cho route (re-export)."""

from app.db.database import get_db

__all__ = ["get_db"]
