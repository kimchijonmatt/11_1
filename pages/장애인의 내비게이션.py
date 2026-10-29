import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
import google.generativeai as genai
from PIL import Image

# 1. 페이지 기본 설정 (페이지 타이틀 수정)
st.set_page_config(
    page_title="장애인을 위한 길안내 서비스",
    page_icon="♿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. 고대비 & 접근성 중심 커스텀 CSS
st.markdown("""
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
""", unsafe_allow_html=True)

# 3. Gemini API 초기화
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", None)
ai_enabled = False

if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-2.5-flash-lite')
        ai_enabled = True
    except Exception as e:
        st.error(f"Gemini API 연동 중 오류 발생: {e}")

# 4. 세션 데이터 초기화
if 'reports' not in st.session_state:
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

# 5. 상단 헤더 (요청하신 타이틀 적용)
st.markdown("""
    <div class="header-box">
        <h1>♿ 장애인을 위한 길안내 서비스</h1>
        <p>교통약자·휠체어 이용자·시각장애인을 위한 접근성 중심 무장애 내비게이션</p>
    </div>
""", unsafe_allow_html=True)

# 6. 메인 탭
tab1, tab2, tab3 = st.tabs(["🗺️ 무장애 길찾기", "📍 시설 정보 & 위험 제보", "🤖 AI 이동 도우미"])

# ---------------------------------------------------------
# TAB 1: 무장애 길찾기
# ---------------------------------------------------------
with tab1:
    col_input, col_result = st.columns([1, 2], gap="medium")
    
    with col_input:
        st.markdown("""
            <div class="custom-card">
                <div class="card-title">🔍 경로 조건 설정</div>
            </div>
        """, unsafe_allow_html=True)
        
        start_p = st.text_input("출발지", value="서울역", key="start_p")
        end_p = st.text_input("목적지", value="광화문광장", key="end_p")
        
        user_mode = st.radio(
            "이동 유형",
            ["♿ 휠체어 이용자 (경사로·엘리베이터)", "🦯 시각장애인 (음향신호·점자블록)", "👶 유모차·고령자 (계단 피하기)"]
        )
        
        st.write("---")
        avoid_stairs = st.checkbox("계단 완벽 제거", value=True)
        avoid_slopes = st.checkbox("급경사 구간 회피", value=True)
        
        find_btn = st.button("🚀 무장애 경로 탐색", use_container_width=True)

    with col_result:
        if find_btn:
            st.markdown(f"""
                <div class="custom-card">
                    <div class="card-title">✨ [{start_p}] ➔ [{end_p}] 최적 안전 경로</div>
                    <p style="color: #6C757D; margin-bottom: 0;">선택 모드: <b>{user_mode}</b></p>
                </div>
            """, unsafe_allow_html=True)
            
            # 요약 지표
            m1, m2, m3 = st.columns(3)
            m1.metric("총 이동거리", "1.8 km")
            m2.metric("예상 소요시간", "약 25분")
            m3.metric("안전 지수", "98점 (계단 0개)")
            
            # 텍스트 안내
            st.markdown("""
            **📌 단계별 상세 이동 가이드**
            1. **[출발]** 서울역 1번 출구 엘리베이터를 통해 지상 보도로 이동합니다.
            2. **[평지]** 300m 직선 보도 이동 (보도폭 2.5m 이상, 턱 없음).
            3. **[횡단보도]** 음향 신호기가 설치된 횡단보도를 통해 안전하게 건넙니다.
            4. **[도착]** 광화문광장 지상 무장애 경사로로 최종 접근합니다.
            """)
            
            # 지도 생성 (width/height 오류 방지 처리 적용)
            m = folium.Map(location=[37.5660, 126.9750], zoom_start=14)
            folium.Marker([37.5559, 126.9723], popup="출발지: 서울역", icon=folium.Icon(color="green", icon="play")).add_to(m)
            folium.Marker([37.5759, 126.9768], popup="목적지: 광화문광장", icon=folium.Icon(color="red", icon="flag")).add_to(m)
            
            route_coords = [
                [37.5559, 126.9723],
                [37.5620, 126.9750],
                [37.5665, 126.9780],
                [37.5759, 126.9768]
            ]
            folium.PolyLine(route_coords, color="#005A9C", weight=7, opacity=0.85, tooltip="추천 경로").add_to(m)
            st_folium(m, use_container_width=True, height=380)
        else:
            st.info("👈 출발지와 목적지를 설정한 후 [무장애 경로 탐색] 버튼을 눌러주세요.")
            default_m = folium.Map(location=[37.5665, 126.9780], zoom_start=13)
            st_folium(default_m, use_container_width=True, height=420)

# ---------------------------------------------------------
# TAB 2: 편의시설 및 위험 제보 Map
# ---------------------------------------------------------
