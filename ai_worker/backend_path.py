"""Nạp package `app` từ thư mục backend (cùng database với API)."""

from __future__ import annotations

import sys
from pathlib import Path


def ensure_backend_on_path() -> Path:
    root = Path(__file__).resolve().parents[1]
    backend = root / "backend"
    b = str(backend)
    if b not in sys.path:
        sys.path.insert(0, b)
    return backend
