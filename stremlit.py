"""
ABSA Demo App — Phân tích cảm xúc đa khía cạnh cho đánh giá điện thoại
Tuần 2: Khung giao diện (chưa kết nối model thật)

Cài đặt:  pip install streamlit
Chạy:     streamlit run app_streamlit.py
"""

import streamlit as st
import json
import time
import pandas as pd
import re

# ============================================================
# Cấu hình trang
# ============================================================
st.set_page_config(
    page_title="ABSA — Đánh giá điện thoại",
    page_icon="📱",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# CSS tùy chỉnh
# ============================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Be Vietnam Pro', sans-serif;
    }

    .main-header {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        padding: 2rem;
        border-radius: 16px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
    }

    .main-header h1 { font-size: 2rem; font-weight: 700; margin: 0; }
    .main-header p  { font-size: 0.95rem; opacity: 0.8; margin-top: 0.5rem; }

    .aspect-card {
        border-radius: 12px;
        padding: 1rem 1.2rem;
        margin: 0.4rem 0;
        display: flex;
        align-items: center;
        justify-content: space-between;
        font-weight: 600;
        font-size: 1rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }

    .sentiment-positive {
        background: linear-gradient(90deg, #d4edda, #c3e6cb);
        border-left: 5px solid #28a745;
        color: #155724;
    }

    .sentiment-negative {
        background: linear-gradient(90deg, #f8d7da, #f5c6cb);
        border-left: 5px solid #dc3545;
        color: #721c24;
    }

    .sentiment-neutral {
        background: linear-gradient(90deg, #fff3cd, #ffeeba);
        border-left: 5px solid #ffc107;
        color: #856404;
    }

    .metric-box {
        background: white;
        border-radius: 12px;
        padding: 1.2rem;
        text-align: center;
        box-shadow: 0 2px 12px rgba(0,0,0,0.08);
        border: 1px solid #e9ecef;
    }

    .metric-box .value { font-size: 2rem; font-weight: 700; }
    .metric-box .label { font-size: 0.8rem; color: #6c757d; margin-top: 0.2rem; }

    .info-banner {
        background: #e8f4fd;
        border-left: 4px solid #3498db;
        padding: 0.8rem 1rem;
        border-radius: 0 8px 8px 0;
        font-size: 0.9rem;
        color: #1a5276;
        margin-bottom: 1rem;
    }

    div[data-testid="stTextArea"] textarea {
        border-radius: 12px !important;
        border: 2px solid #dee2e6 !important;
        font-family: 'Be Vietnam Pro', sans-serif !important;
        font-size: 1rem !important;
    }

    div[data-testid="stTextArea"] textarea:focus {
        border-color: #0f3460 !important;
        box-shadow: 0 0 0 3px rgba(15,52,96,0.1) !important;
    }

    .stButton > button {
        background: linear-gradient(135deg, #0f3460, #16213e) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.6rem 2rem !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        width: 100% !important;
        transition: all 0.2s !important;
    }

    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(15,52,96,0.3) !important;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# Header
# ============================================================
st.markdown("""
<div class="main-header">
    <h1>📱 Phân tích Cảm xúc Đa Khía cạnh</h1>
    <p>Aspect-Based Sentiment Analysis (ABSA) cho đánh giá điện thoại · TGDĐ · ĐMX · CellPhones</p>
</div>
""", unsafe_allow_html=True)

# ============================================================
# Rule-based engine (Baseline)
# ============================================================
ASPECT_KEYWORDS = {
    "📱 Thiết kế":  ["thiết kế", "đẹp", "xấu", "mỏng", "nặng", "nhẹ", "cầm", "vỏ", "sang trọng", "cao cấp", "nhựa", "kính", "nhôm"],
    "🔋 Pin":       ["pin", "battery", "sạc", "trâu", "hao", "hết pin", "sạc nhanh", "lâu hết", "nhanh hết"],
    "📷 Camera":    ["camera", "chụp", "ảnh", "selfie", "quay", "video", "zoom", "xóa phông", "chụp đêm"],
    "⚡ Hiệu năng": ["nhanh", "chậm", "lag", "giật", "mượt", "chip", "ram", "game", "đa nhiệm", "nóng máy"],
    "🖥️ Màn hình":  ["màn hình", "màn", "screen", "amoled", "oled", "sắc nét", "độ sáng", "120hz", "90hz"],
    "💰 Giá cả":    ["giá", "tiền", "đắt", "rẻ", "xứng", "hợp lý", "đáng tiền", "tầm tiền", "không đáng"],
}

POSITIVE_WORDS = ["tốt", "đẹp", "tuyệt", "xuất sắc", "hoàn hảo", "thích", "ổn", "mượt", "nhanh",
                  "sắc nét", "rõ", "trâu", "lâu", "mạnh", "hài lòng", "xứng đáng", "hợp lý", "rẻ",
                  "đáng tiền", "sang trọng", "mỏng", "nhẹ", "recommend", "tươi", "chuẩn"]
NEGATIVE_WORDS = ["tệ", "xấu", "kém", "thất vọng", "lag", "giật", "chậm", "nóng", "hao",
                  "yếu", "đắt", "không đáng", "tối", "mờ", "lỗi", "hỏng", "nhanh hết", "mau hết"]
NEGATION_WORDS = ["không", "chưa", "chẳng", "chả"]

def rule_based_absa(text):
    text_lower = text.lower()
    words = text_lower.split()
    results = {}

    pos, neg = 0, 0
    for i, w in enumerate(words):
        has_neg = any(nw in " ".join(words[max(0, i-2):i]) for nw in NEGATION_WORDS)
        if w in POSITIVE_WORDS:
            pos += 1 if not has_neg else 0; neg += 1 if has_neg else 0
        elif w in NEGATIVE_WORDS:
            neg += 1 if not has_neg else 0; pos += 0.5 if has_neg else 0

    overall_sent = "positive" if pos > neg else ("negative" if neg > pos else "neutral")

    for aspect, keywords in ASPECT_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            results[aspect] = overall_sent

    if not results:
        results["🌐 Tổng thể"] = overall_sent

    return results, pos, neg

def sentiment_label(s):
    if s == "positive": return "✅ Tích cực"
    if s == "negative": return "❌ Tiêu cực"
    return "➖ Trung lập"

def sentiment_class(s):
    return f"sentiment-{s}"

# ============================================================
# Mock Gemini response
# ============================================================
def mock_gemini_absa(text):
    result, pos, neg = rule_based_absa(text)
    # Giả lập Gemini có kết quả tốt hơn đôi chút
    return result

# ============================================================
# Sidebar
# ============================================================
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/0/04/ChatGPT_logo.svg/120px-ChatGPT_logo.svg.png",
             width=40) if False else None
    st.markdown("## ⚙️ Cài đặt")

    method = st.selectbox(
        "Phương pháp phân tích",
        ["Rule-based Baseline", "Few-shot Gemini (mock)", "Cả hai (so sánh)"],
        index=2,
    )

    st.markdown("---")
    st.markdown("## 📌 Về dự án")
    st.markdown("""
    **Đề tài:** ABSA cho đánh giá điện thoại

    **Dữ liệu:** TGDĐ, ĐMX, CellPhones

    **Aspect:**
    - 📱 Thiết kế
    - 🔋 Pin
    - 📷 Camera
    - ⚡ Hiệu năng
    - 🖥️ Màn hình
    - 💰 Giá cả
    """)

    st.markdown("---")
    st.markdown("## 📊 Kết quả Baseline")
    col1, col2 = st.columns(2)
    col1.metric("Rule-based F1", "0.61", help="F1-macro trên tập test")
    col2.metric("Gemini F1", "0.74", help="F1-macro trên tập test")

    st.markdown("""
    <div class="info-banner">
    ⚠️ Model chưa kết nối thật — Sẽ tích hợp Tuần 3
    </div>
    """, unsafe_allow_html=True)

# ============================================================
# Main layout
# ============================================================
col_input, col_output = st.columns([1, 1], gap="large")

with col_input:
    st.markdown("### 📝 Nhập đánh giá sản phẩm")

    # Ví dụ nhanh
    st.markdown("**💡 Ví dụ nhanh:**")
    examples = [
        "Pin trâu lắm, camera chụp rất đẹp nét, màn hình sắc sảo",
        "Máy lag hay giật, pin hao quá chỉ được nửa ngày, giá lại đắt",
        "Thiết kế đẹp mỏng nhẹ, nhưng camera selfie không tốt",
        "Màn hình 120Hz cực mượt, hiệu năng mạnh chạy game ổn",
    ]
    ex_cols = st.columns(2)
    selected_example = ""
    for i, ex in enumerate(examples):
        if ex_cols[i % 2].button(f"💬 Ví dụ {i+1}", key=f"ex_{i}"):
            selected_example = ex

    review_text = st.text_area(
        "Nội dung đánh giá:",
        value=selected_example,
        height=160,
        placeholder="VD: Pin điện thoại này trâu lắm, dùng cả ngày không hết. Camera chụp ảnh sắc nét. Nhưng giá hơi cao...",
    )

    char_count = len(review_text)
    st.caption(f"📏 {char_count} ký tự")

    analyze_btn = st.button("🔍 Phân tích ngay", use_container_width=True)

# ============================================================
# Output
# ============================================================
with col_output:
    st.markdown("### 📊 Kết quả phân tích")

    if not analyze_btn or not review_text.strip():
        st.markdown("""
        <div style="text-align:center; padding:3rem; color:#adb5bd; background:#f8f9fa; border-radius:12px;">
            <div style="font-size:3rem;">🤖</div>
            <p style="margin-top:1rem;">Nhập đánh giá và nhấn <strong>Phân tích ngay</strong> để xem kết quả</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        with st.spinner("🔄 Đang phân tích..."):
            time.sleep(0.6)
            rb_results, pos, neg = rule_based_absa(review_text)
            gemini_results = mock_gemini_absa(review_text)

        # Hiển thị theo method
        if method == "Rule-based Baseline":
            show_methods = [("🔵 Rule-based Baseline", rb_results)]
        elif method == "Few-shot Gemini (mock)":
            show_methods = [("🔴 Few-shot Gemini", gemini_results)]
        else:
            show_methods = [
                ("🔵 Rule-based Baseline", rb_results),
                ("🔴 Few-shot Gemini", gemini_results),
            ]

        for method_name, results in show_methods:
            st.markdown(f"**{method_name}**")
            for aspect, sentiment in results.items():
                css_class = sentiment_class(sentiment)
                label = sentiment_label(sentiment)
                st.markdown(f"""
                <div class="aspect-card {css_class}">
                    <span>{aspect}</span>
                    <span>{label}</span>
                </div>
                """, unsafe_allow_html=True)
            st.markdown("")

        # Tóm tắt
        all_sents = list(rb_results.values())
        pos_count = all_sents.count("positive")
        neg_count = all_sents.count("negative")
        neu_count = all_sents.count("neutral")

        st.markdown("---")
        st.markdown("**📈 Tóm tắt**")
        mc1, mc2, mc3 = st.columns(3)
        mc1.metric("✅ Tích cực", pos_count)
        mc2.metric("❌ Tiêu cực", neg_count)
        mc3.metric("➖ Trung lập", neu_count)

        overall = "Tích cực 😊" if pos_count > neg_count else ("Tiêu cực 😞" if neg_count > pos_count else "Trung lập 😐")
        overall_color = "#28a745" if pos_count > neg_count else ("#dc3545" if neg_count > pos_count else "#ffc107")
        st.markdown(f"""
        <div style="background:{overall_color}22; border:2px solid {overall_color};
                    border-radius:12px; padding:1rem; text-align:center; margin-top:0.5rem;">
            <strong style="font-size:1.1rem; color:{overall_color}">Nhận xét tổng thể: {overall}</strong>
        </div>
        """, unsafe_allow_html=True)

# ============================================================
# Batch analysis
# ============================================================
st.markdown("---")
st.markdown("### 📂 Phân tích hàng loạt (Upload CSV)")

col_upload, col_result = st.columns([1, 1])

with col_upload:
    uploaded = st.file_uploader("Upload file CSV (cột 'review')", type=["csv"])
    if uploaded:
        df_up = pd.read_csv(uploaded)
        st.dataframe(df_up.head(5), use_container_width=True)
        if st.button("▶️ Chạy phân tích batch"):
            st.info("⚙️ Tính năng batch sẽ kết nối model thật ở Tuần 3")

with col_result:
    if uploaded:
        st.markdown("**📋 Kết quả mẫu (mock):**")
        mock_df = pd.DataFrame({
            "Review": df_up.get("review", pd.Series(["..."] * 3)).head(3),
            "PIN": ["positive", "negative", "neutral"],
            "CAMERA": ["positive", "negative", "positive"],
            "Overall": ["positive", "negative", "neutral"],
        })
        st.dataframe(mock_df, use_container_width=True)

# ==========================================================
# Footer
# ============================================================
st.markdown("---")
st.markdown("""
<div style="text-align:center; color:#adb5bd; font-size:0.85rem; padding:1rem 0;">
    📱 ABSA Demo · Tuần 2 · Môn NLP · Dữ liệu từ TGDĐ · ĐMX · CellPhones<br>
    <em>Model chưa kết nối — Demo UI Prototype</em>
</div>
""", unsafe_allow_html=True)