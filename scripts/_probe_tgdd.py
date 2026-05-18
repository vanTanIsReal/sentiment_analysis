import json
import re
from pathlib import Path

import httpx

url = "https://www.thegioididong.com/dtdd/iphone-15-plus"
r = httpx.get(
    url,
    headers={"User-Agent": "Mozilla/5.0", "Accept-Language": "vi-VN"},
    timeout=30,
    follow_redirects=True,
)
html = r.text
print("len html", len(html))
for pat in ["__NEXT_DATA__", "comment", "rating", "ProductComment", "getcomment", "apiweb"]:
    print(pat, html.lower().count(pat.lower()))
m = re.search(r'id="__NEXT_DATA__"[^>]*>(\{.*?\})</script>', html, re.DOTALL)
if not m:
    # try other script json blobs
    scripts = re.findall(r"<script[^>]*>(\{[^<]{200,})</script>", html)
    print("json scripts", len(scripts))
    apis = re.findall(r"https?://[^\"'\s]+(?:comment|rating|Comment|avacomment|mwgcart)[^\"'\s]*", html, re.I)
    print("html api urls unique", len(set(apis)))
    for u in sorted(set(apis))[:30]:
        if ".js" not in u and ".css" not in u and ".png" not in u and ".jpg" not in u and ".svg" not in u:
            print(" ", u)
    # product id in html
    for pat in [r"productId[\"']?\s*[:=]\s*[\"']?(\d+)", r"ProductId[\"']?\s*[:=]\s*[\"']?(\d+)", r"siteProductId[\"']?\s*[:=]\s*[\"']?(\d+)"]:
        found = re.findall(pat, html, re.I)
        if found:
            print(pat, list(dict.fromkeys(found))[:5])
    # avacomment config
    for pat in [r"avacomment[^\"']{0,80}", r"/api/[^\"']+comment[^\"']*", r"GetComment[^\"']*", r"getListComment[^\"']*"]:
        hits = re.findall(pat, html, re.I)
        if hits:
            print("hits", pat, hits[:5])
    out = Path("data/raw/tgdd/_probe_snippet.txt")
    out.parent.mkdir(parents=True, exist_ok=True)
    apis2 = re.findall(r'["\']([^"\']*(?:Comment|comment|Rating|rating)[^"\']*)["\']', html)
    out.write_text("\n".join(sorted(set(apis2))[:200]), encoding="utf-8")
    print("wrote", out, "lines", len(set(apis2)))
    js_url = "https://cdn.tgdd.vn/mwgcart/avacomment/js/bundle/comment.min.v20210712737.js"
    js = httpx.get(js_url, timeout=30).text
    apis3 = sorted(set(re.findall(r"https?://[^\"']+", js)))
    for x in apis3:
        if any(k in x.lower() for k in ("comment", "rating", "api")):
            print("js api", x)
    # try common MWG endpoints
    pid = "303891"
    headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/json", "Referer": url}
    candidates = [
        f"https://www.thegioididong.com/commentnew/cmtv2/index?productId={pid}&pageIndex=0&pageSize=20",
        f"https://www.thegioididong.com/commentnew/cmtv2/GetComments?productId={pid}&pageIndex=0&pageSize=20",
        f"https://www.thegioididong.com/commentnew/GetComments?productId={pid}&pageIndex=0&pageSize=20",
    ]
    for c in candidates:
        try:
            r2 = httpx.get(c, headers=headers, timeout=15)
            print("GET", c, r2.status_code, r2.text[:200].replace("\n", " "))
        except Exception as e:
            print(c, "err", e)
    post_urls = [
        "https://www.thegioididong.com/commentnew/cmtv2/GetComments",
        "https://www.thegioididong.com/commentnew/GetComments",
    ]
    body = {"productId": int(pid), "pageIndex": 0, "pageSize": 20}
    for c in post_urls:
        try:
            r2 = httpx.post(c, json=body, headers=headers, timeout=15)
            print("POST", c, r2.status_code, r2.text[:200].replace("\n", " "))
        except Exception as e:
            print(c, "err", e)
    # grep js for GetComment paths
    paths = sorted(set(re.findall(r"/commentnew/[a-zA-Z0-9_/]+", js)))
    print("js paths", paths[:30])
    fns = sorted(set(re.findall(r"(?:Get|Load|Submit|Fetch)[A-Za-z]{3,30}", js)))
    print("js fn sample", [x for x in fns if "omment" in x or "ating" in x][:40])
    # save js excerpt around productId
    idx = js.find("productId")
    Path("data/raw/tgdd/_probe_js.txt").write_text(js[idx : idx + 3000], encoding="utf-8")
    print("wrote js excerpt")
    raise SystemExit(0)
d = json.loads(m.group(1))
s = json.dumps(d, ensure_ascii=False)
for kw in ["comment", "rating", "review", "ProductId", "productId", "SiteProduct"]:
    print(kw, s.lower().count(kw.lower()))
ids = re.findall(r'"(?:productId|ProductId|idProduct)":\s*(\d+)', s[:800000])
print("product ids", list(dict.fromkeys(ids))[:10])
apis = re.findall(r"https?://[^\"']+(?:comment|rating|review)[^\"']*", s, re.I)
print("api urls", apis[:15])
# dump keys at shallow level
props = d.get("props", {})
print("props keys", list(props.keys())[:20])
