"""Parse HTML / JSON response từ TGDĐ."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from bs4 import BeautifulSoup


@dataclass
class ParsedReview:
    text: str
    rating: int | None
    author: str | None


def extract_next_data_json(html: str) -> dict[str, Any] | None:
    m = re.search(
        r'<script[^>]*id="__NEXT_DATA__"[^>]*>\s*(\{.*?\})\s*</script>',
        html,
        re.DOTALL,
    )
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except json.JSONDecodeError:
        return None


def iter_reviews_from_html(html: str) -> list[ParsedReview]:
    """Tách đánh giá: ưu tiên __NEXT_DATA__ nếu có cấu trúc reviews; fallback comment block."""
    out: list[ParsedReview] = []
    data = extract_next_data_json(html)
    if data:
        # Dò đệ quy key "comment" / "reviews" (cấu trúc site có thể đổi — chỉnh nếu cần)
        blob = json.dumps(data)

        def walk(o: Any) -> None:
            if isinstance(o, dict):
                for k, v in o.items():
                    lk = k.lower()
                    if lk in ("comments", "reviews", "ratingcomments") and isinstance(v, list):
                        for item in v:
                            if isinstance(item, dict):
                                txt = (
                                    item.get("content")
                                    or item.get("CommentContent")
                                    or item.get("text")
                                    or item.get("body")
                                )
                                if isinstance(txt, str) and txt.strip():
                                    r = item.get("rating") or item.get("score")
                                    rating = int(r) if isinstance(r, (int, float)) else None
                                    auth = item.get("author") or item.get("userName")
                                    a = str(auth) if auth else None
                                    out.append(ParsedReview(text=txt.strip(), rating=rating, author=a))
                    walk(v)
            elif isinstance(o, list):
                for x in o:
                    walk(x)

        walk(data)
        if out:
            return out

    soup = BeautifulSoup(html, "lxml")
    for node in soup.select("[class*='comment'], [class*='review'], .cmt__content, .review-content"):
        t = node.get_text(" ", strip=True)
        if len(t) > 15:
            out.append(ParsedReview(text=t, rating=None, author=None))
    return out


def extract_product_meta(html: str) -> dict[str, str | None]:
    soup = BeautifulSoup(html, "lxml")
    title = soup.title.string.strip() if soup.title and soup.title.string else None
    og = soup.find("meta", property="og:url")
    url = og["content"] if og and og.get("content") else None
    return {"title": title, "og_url": url}
