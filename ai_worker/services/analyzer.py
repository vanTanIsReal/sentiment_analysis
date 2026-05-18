"""Phân tích đa khía cạnh, parse JSON kết quả."""

from __future__ import annotations

import json
import re
from pathlib import Path

from ai_worker.services.llm_client import complete_chat


def _load_few_shot() -> str:
    p = Path(__file__).resolve().parents[1] / "prompts" / "few_shot.txt"
    if p.is_file():
        return p.read_text(encoding="utf-8")
    return ""


def analyze_review_text(text: str) -> list[dict]:
    """
    Trả về danh sách dict: aspect, sentiment (positive|negative|neutral),
    confidence (0-1, optional), quote (optional).
    """
    few = _load_few_shot()
    system = (
        "Bạn là hệ thống phân tích cảm xúc theo khía cạnh cho đánh giá sản phẩm điện thoại.\n"
        "Chỉ trả về một mảng JSON hợp lệ, không markdown, không giải thích thêm.\n"
        "Mỗi phần tử: {\"aspect\": str, \"sentiment\": \"positive\"|\"negative\"|\"neutral\", "
        "\"confidence\": number tùy chọn 0-1, \"quote\": string tùy chọn (trích từ đánh giá)}.\n"
        "Các khía cạnh gợi ý: màn_hình, pin, camera, hiệu_năng, thiết_kế, loa, giá_cả, phục_vụ, v.v."
    )
    if few.strip():
        system += "\n\nVí dụ few-shot:\n" + few

    user = f"Đánh giá cần phân tích:\n\"\"\"\n{text.strip()}\n\"\"\""

    raw = complete_chat(system, user).strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.IGNORECASE)
    raw = re.sub(r"\s*```$", "", raw)
    data = json.loads(raw)
    if not isinstance(data, list):
        raise ValueError("LLM không trả về mảng JSON")
    out: list[dict] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        aspect = str(item.get("aspect", "")).strip()
        sentiment = str(item.get("sentiment", "")).strip().lower()
        if aspect and sentiment in ("positive", "negative", "neutral"):
            rec = {"aspect": aspect, "sentiment": sentiment}
            if item.get("confidence") is not None:
                try:
                    rec["confidence"] = float(item["confidence"])
                except (TypeError, ValueError):
                    pass
            if item.get("quote"):
                rec["quote"] = str(item["quote"])[:2000]
            out.append(rec)
    return out
