"""
Crawl đánh giá sản phẩm TGDD (Playwright).

Mỗi bản ghi output:
  review, rating (1-5), product, source, date

Chạy từ thư mục gốc repo:
  python -m crawler.crawl_tgdd
  python -m crawler.crawl_tgdd --urls-file crawler/product_urls.txt

Điền link trong: crawler/product_urls.txt
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import sys
import time
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

try:
    from config import (
        CRAWL_DELAY_SEC,
        CRAWL_SOURCE,
        HEADLESS_MODE,
        MAX_COMMENT_PAGES,
        OUTPUT_DIR,
        PRODUCT_URLS_FILE,
    )
except ImportError:
    from config import (
        CRAWL_DELAY_SEC,
        CRAWL_SOURCE,
        HEADLESS_MODE,
        MAX_COMMENT_PAGES,
        OUTPUT_DIR,
        PRODUCT_URLS_FILE,
    )

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

OUTPUT_FIELDS = ("review", "rating", "product", "source", "date")

# TGDD trang /danh-gia: mỗi đánh giá trong li.par
EXTRACT_REVIEWS_JS = """
() => {
  const rows = [];
  const items = document.querySelectorAll('#scrollList li.par, ul.comment-list > li.par');
  for (const item of items) {
    const reviewEl = item.querySelector('.cmt-txt');
    if (!reviewEl) continue;
    const review = (reviewEl.innerText || '').trim();
    if (review.length < 10) continue;

    let rating = null;
    const starBuy = item.querySelectorAll('.cmt-top-star .iconcmt-starbuy, .iconcmt-starbuy').length;
    if (starBuy >= 1 && starBuy <= 5) {
      rating = starBuy;
    }

    let date = null;
    for (const sel of ['.cmt-time', '.txt-time', '.time-line', '.time']) {
      const el = item.querySelector(sel);
      if (el) {
        const t = (el.innerText || '').trim();
        if (t) { date = t; break; }
      }
    }
    if (!date) {
      const m = (item.innerText || '').match(/\\d{1,2}\\/\\d{1,2}\\/\\d{2,4}/);
      if (m) date = m[0];
    }
    if (!date) {
      const usage = item.querySelector('.txt-intro');
      if (usage) {
        const t = (usage.innerText || '').trim();
        if (/đã dùng|ngày|tháng|tuần/i.test(t) && !/giới thiệu/i.test(t)) {
          date = t;
        }
      }
    }

    rows.push({ review, rating, date });
  }
  return rows;
}
"""

EXTRACT_PRODUCT_JS = """
() => {
  const title = document.querySelector('.boxrate__title, h2.boxrate__title');
  if (title) {
    return (title.innerText || '')
      .replace(/^\\d+\\s*đánh giá\\s*/i, '')
      .trim();
  }
  const h1 = document.querySelector('h1');
  return (h1?.innerText || document.title || '').trim();
}
"""


def load_urls_from_file(path: Path) -> list[str]:
    if not path.is_file():
        logger.warning("Khong tim thay file URL: %s", path)
        return []
    urls: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        urls.append(line)
    return urls


def resolve_product_urls(cli_urls: list[str], urls_file: Path | None) -> list[str]:
    if cli_urls:
        return cli_urls
    path = urls_file or PRODUCT_URLS_FILE
    from_file = load_urls_from_file(path)
    if from_file:
        logger.info("Doc %d URL tu %s", len(from_file), path)
        return from_file
    logger.warning("Khong co URL — them link vao %s hoac truyen tren dong lenh.", path)
    return []


def to_review_url(seed: str) -> str:
    return seed if "/danh-gia" in seed else f"{seed.rstrip('/')}/danh-gia"


def clean_product_name(raw: str) -> str:
    name = raw.strip()
    for sep in [" - ", " | ", " giá ", " – "]:
        if sep in name:
            name = name.split(sep)[0].strip()
    if name.lower().startswith("điện thoại "):
        name = name[11:].strip()
    if name.lower().startswith("danh gia "):
        name = name[9:].strip()
    return name or "Unknown"


def get_product_name(page: Page) -> str:
    raw = page.evaluate(EXTRACT_PRODUCT_JS)
    return clean_product_name(str(raw))


def crawl_dynamic_reviews(
    page: Page,
    url: str,
    *,
    product: str,
    source: str,
    max_pages: int = MAX_COMMENT_PAGES,
) -> list[dict]:
    rows: list[dict] = []
    seen: set[tuple[str, str]] = set()

    logger.info("Dang tai: %s", url)
    page.goto(url, timeout=60_000, wait_until="domcontentloaded")
    try:
        page.wait_for_selector(".cmt-txt, #scrollList li.par", timeout=20_000)
    except Exception:
        logger.warning("  Khong thay danh sach comment — thu tiep tuc...")
    page.wait_for_timeout(2000)

    product_name = product if product != "Unknown" else get_product_name(page)
    if product_name == "Unknown":
        product_name = clean_product_name(page.title())

    for current_page in range(max_pages):
        logger.info("  Trang binh luan %d/%d", current_page + 1, max_pages)

        extracted: list[dict] = page.evaluate(EXTRACT_REVIEWS_JS)
        for item in extracted:
            review = (item.get("review") or "").strip()
            if len(review) < 10:
                continue
            key = (product_name, review)
            if key in seen:
                continue
            seen.add(key)

            rating_raw = item.get("rating")
            rating: int | None = None
            if rating_raw is not None:
                try:
                    r = int(rating_raw)
                    if 1 <= r <= 5:
                        rating = r
                except (TypeError, ValueError):
                    pass

            date_raw = item.get("date")
            date: str | None = None
            if date_raw:
                date = str(date_raw).strip() or None

            rows.append(
                {
                    "review": review,
                    "rating": rating,
                    "product": product_name,
                    "source": source,
                    "date": date,
                }
            )

        next_button = page.query_selector(".pagComment a:not(.active)")
        if next_button and next_button.is_visible():
            next_button.click()
            page.wait_for_timeout(2000)
        else:
            logger.info("  Het trang binh luan.")
            break

    logger.info("  -> %d danh gia (%s)", len(rows), product_name)
    return rows


def write_outputs(all_rows: list[dict], out_dir: Path) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = out_dir / "crawl_snapshot.jsonl"
    csv_path = out_dir / "crawl_snapshot.csv"

    def row_for_export(r: dict) -> dict:
        return {
            "review": r["review"],
            "rating": r["rating"] if r["rating"] is not None else "",
            "product": r["product"],
            "source": r["source"],
            "date": r["date"] or "",
        }

    export_rows = [row_for_export(r) for r in all_rows]

    with jsonl_path.open("w", encoding="utf-8") as f:
        for r in all_rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(OUTPUT_FIELDS))
        writer.writeheader()
        writer.writerows(export_rows)

    return jsonl_path, csv_path


def run(seed_urls: list[str]) -> Path:
    if not seed_urls:
        raise SystemExit(
            f"Khong co URL de crawl. Sua file {PRODUCT_URLS_FILE} hoac truyen URL tren dong lenh."
        )

    all_rows: list[dict] = []
    source = CRAWL_SOURCE

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=HEADLESS_MODE)
        page = browser.new_page(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
        )
        try:
            for i, seed in enumerate(seed_urls):
                if i > 0:
                    time.sleep(CRAWL_DELAY_SEC)
                review_url = to_review_url(seed)
                logger.info("[%d/%d] %s", i + 1, len(seed_urls), seed)
                try:
                    all_rows.extend(
                        crawl_dynamic_reviews(
                            page,
                            review_url,
                            product="Unknown",
                            source=source,
                        )
                    )
                except Exception as e:
                    logger.error("Loi crawl %s: %s", seed, e)
        finally:
            browser.close()

    jsonl_path, csv_path = write_outputs(all_rows, OUTPUT_DIR)
    logger.info("Da ghi %d danh gia -> %s va %s", len(all_rows), jsonl_path, csv_path)
    return jsonl_path


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Crawl danh gia TGDD (Playwright)")
    parser.add_argument(
        "urls",
        nargs="*",
        help="URL san pham (neu bo trong se doc tu product_urls.txt)",
    )
    parser.add_argument(
        "--urls-file",
        type=Path,
        default=None,
        help=f"File danh sach URL (mac dinh: {PRODUCT_URLS_FILE})",
    )
    args = parser.parse_args(argv)
    urls = resolve_product_urls(args.urls, args.urls_file)
    run(urls)


if __name__ == "__main__":
    main(sys.argv[1:])
