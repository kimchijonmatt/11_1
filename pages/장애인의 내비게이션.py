import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
import google.generativeai as genai
from PIL import Image

# 1. 페이지 기본 설정
st.set_page_config(
    page_title="장애인을 위한 길안내 서비스",
    page_icon="♿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. 커스텀 CSS
css_code = """
<style>
.stApp {
    background-color: #F8F9FA;
}
.header-box {
    background: linear-gradient(135deg, #005A9C 0%, #003B66 100%);
    color: white;
    padding: 24px 30px;
    border-radius: 16px;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
    margin-bottom: 25px;
}
.header-box h1 {
    color: #FFFFFF !important;
    font-size: 2.1rem !important;
    font-weight: 800 !important;
    margin: 0 0 8px 0 !important;
}
.header-box p {
    color: #E2E8F0 !important;
    font-size: 1.05rem !important;
    margin: 0 !important;
}
.custom-card {
    background-color: #FFFFFF;
    padding: 20px;
    border-radius: 12px;
    border: 1px solid #E9ECEF;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    margin-bottom: 20px;
}
.card-title {
    font-size: 1.15rem;
    font-weight: 700;
    color: #005A9C;
    margin-bottom: 12px;
    display: flex;
    align-items: center;
    gap: 8px;
}
.stTabs [data-baseweb="tab-list"] {
    gap: 12px;
    background-color: transparent;
}
.stTabs [data-baseweb="tab"] {
    height: 50px;
    white-space: pre-wrap;
    background-color: #FFFFFF;
    border-radius: 10px;
    color: #495057;
    font-weight: 600;
    border: 1px solid #DEE2E6;
    padding: 0px 20px;
}
.stTabs [aria-selected="true"] {
    background-color: #005A9C !important;
    color: #FFFFFF !important;
    border-color: #005A9C !important;
}
.stButton > button {
    background-color: #005A9C;
    color: white;
    font-weight: 700;
    font-size: 1rem;
    border-radius: 8px;
    border: none;
    padding: 0.6rem 1rem;
    transition: all 0.2s ease;
}
.stButton > button:hover {
    background-color: #004070;
    color: white;
    box-shadow: 0 4px 12px rgba(0,90,156,0.3);
}
</style>
"""
st.markdown(css_code, unsafe_allow_html=True)

# 3. Gemini API 예외 처리
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", None)
ai_enabled = False
model = None

if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-2.5-flash-lite")
        ai_enabled = True
    except Exception as e:
        st.warning(f"Gemini API 연결 중 오류 발생: {e}")

# 4. 세션 데이터 설정
if "reports" not in st.session_state:
    st.session_state.reports = [
        {"lat": 37.5665, "lon": 126.9780, "type": "🚫 엘리베이터 고장", "desc": "시청역 1번 출구 엘리베이터 점검 중"},
        {"lat": 37.5700, "lon": 126.9820, "type": "🚧 공사 구간", "desc": "보도블록 공사로 인해 휠체어 통행 불가"}
    ]

FACILITIES = [
    {"name": "시청역 장애인 화장실", "lat": 37.5662, "lon": 126.9784, "cat": "🚽 화장실"},
    {"name": "광화문역 전동휠체어 충전소", "lat": 37.5715, "lon": 126.9768, "cat": "🔌 충전소"},
    {"name": "덕수궁 입구 경사로", "lat": 37.5658, "lon": 126.9752, "cat": "♿ 경사로"},
    {"name": "서울시청 지하 휠체어 리프트", "lat": 37.5668, "lon": 126.9788, "cat": "🛗 리프트"}
]

# 5. 상단 타이틀
header_html = """
<div class="header-box">
    <h1>♿ 장애인을 위한 길안내 서비스</h1>
    <p>교통약자·휠체어 이용자·시각장애인을 위한 접근성 중심 무장애 내비게이션</p>
</div>
"""
st.markdown(header_html, unsafe_allow_html=True)

# 6. 메인 탭
tab1, tab2, tab3 = st.tabs(["🗺️ 무장애 길찾기", "📍 시설 정보 & 위험 제보", "🤖 AI 이동 도우미"])

# TAB 1: 무장애 길찾기
with tab1:
    col_input, col_result = st.columns([1, 2], gap="medium")
    
    with col_input:
        st.markdown('<div class="custom-card"><div class="card-title">🔍 경로 조건 설정</div></div>', unsafe_allow_html=True)
        
        start_p = st.text_input("출발지", value="서울역", key="start_input")
        end_p = st.text_input("목적지", value="광화문광장", key="end_input")
        
        user_mode = st.radio(
            "이동 유형",
            ["♿ 휠체어 이용자 (경사로·엘리베이터)", "🦯 시각장애인 (음향신호·점자블록)", "👶 유모차·고령자 (계단 피하기)"],
