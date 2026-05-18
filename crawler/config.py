"""Cấu hình URL, delay, output path và thông số Playwright cho crawler."""

from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv

# Load biến môi trường từ file .env (nếu có)
load_dotenv()

# Xác định thư mục gốc của dự án
REPO_ROOT = Path(__file__).resolve().parents[1]

# ==========================================
# 1. CẤU HÌNH ĐẦU VÀO / ĐẦU RA (I/O)
# ==========================================
DEFAULT_SEED_URLS: list[str] = [
    "https://www.thegioididong.com/dtdd-apple-iphone",
    "https://www.thegioididong.com/dtdd-samsung",
]
OUTPUT_DIR: Path = Path(os.getenv("CRAWL_OUTPUT_DIR", str(REPO_ROOT / "data" / "raw" / "tgdd")))

# File danh sách URL (mỗi dòng một link) — ưu tiên khi chạy không truyền URL trên dòng lệnh
PRODUCT_URLS_FILE: Path = Path(
    os.getenv("CRAWL_PRODUCT_URLS_FILE", str(REPO_ROOT / "crawler" / "product_urls.txt"))
)

# Số trang bình luận tối đa mỗi sản phẩm (Playwright bấm Next)
MAX_COMMENT_PAGES: int = int(os.getenv("MAX_COMMENT_PAGES", "10"))

# Nguồn dữ liệu (cột `source` trong file export)
CRAWL_SOURCE: str = os.getenv("CRAWL_SOURCE", "thegioididong.com")


# ==========================================
# 2. CẤU HÌNH GIỚI HẠN (LIMITS) - Rất quan trọng cho BTL
# ==========================================
# Giới hạn số lượng sản phẩm cào mỗi danh mục (tránh cào quá lâu)
MAX_PRODUCTS_TO_CRAWL: int = int(os.getenv("MAX_PRODUCTS_TO_CRAWL", "10"))

# Giới hạn số lượng bình luận tối đa lấy từ 1 sản phẩm
MAX_REVIEWS_PER_PRODUCT: int = int(os.getenv("MAX_REVIEWS_PER_PRODUCT", "50"))


# ==========================================
# 3. CẤU HÌNH TRÌNH DUYỆT (PLAYWRIGHT)
# ==========================================
# Playwright Timeout (Tính bằng mili-giây, 30000 = 30s)
REQUEST_TIMEOUT: float = float(os.getenv("CRAWL_TIMEOUT", "30000"))

# Thời gian nghỉ giữa các lần click/cuộn trang để tránh bị khóa IP
CRAWL_DELAY_SEC: float = float(os.getenv("CRAWL_DELAY_SEC", "2.0"))

# Chế độ chạy ngầm (True = không mở giao diện, False = mở giao diện Chrome để xem)
# Khi code đang test thì để False, khi chạy thật thì đổi thành True
HEADLESS_MODE: bool = os.getenv("HEADLESS_MODE", "False").lower() in ("true", "1", "yes")

USER_AGENT: str = os.getenv(
    "CRAWL_USER_AGENT",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
)