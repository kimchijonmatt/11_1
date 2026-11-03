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
with tab2:
    col_map_view, col_report_form = st.columns([2, 1], gap="medium")
    
    with col_report_form:
        st.markdown("""
            <div class="custom-card">
                <div class="card-title">⚠️ 실시간 위험/장애물 제보</div>
            </div>
        """, unsafe_allow_html=True)
        
        r_type = st.selectbox("위험 유형", ["🚫 엘리베이터 고장", "🚧 공사 구간", "⚠️ 보도블록 파손", "❌ 경사로 막힘", "💬 기타"])
        r_desc = st.text_area("상세 내용 입력", placeholder="예: 3번 출구 엘리베이터가 고장나 점검 중입니다.")
        r_lat = st.number_input("위도 (Lat)", value=37.5670, format="%.4f")
        r_lon = st.number_input("경도 (Lon)", value=126.9790, format="%.4f")
        
        if st.button("📢 위치 제보 등록", use_container_width=True):
            if r_desc.strip():
                st.session_state.reports.append({
                    "lat": r_lat,
                    "lon": r_lon,
                    "type": r_type,
                    "desc": r_desc
                })
                st.success("제보 내용이 지도의 실시간 등록되었습니다.")
            else:
                st.warning("상세 내용을 작성해 주세요.")
                
    with col_map_view:
        st.markdown("##### 📍 편의시설 및 사용자 제보 지도")
        m2 = folium.Map(location=[37.5665, 126.9780], zoom_start=14)
        
        # 편의시설 마커 (Blue)
        for fac in FACILITIES:
            folium.Marker(
                [fac["lat"], fac["lon"]],
                popup=f"<b>{fac['name']}</b><br>{fac['cat']}",
                icon=folium.Icon(color="blue", icon="info-sign")
            ).add_to(m2)
            
        # 제보 마커 (Red)
        for rep in st.session_state.reports:
            folium.Marker(
                [rep["lat"], rep["lon"]],
                popup=f"<b>[제보] {rep['type']}</b><br>{rep['desc']}",
                icon=folium.Icon(color="red", icon="exclamation-sign")
            ).add_to(m2)
            
        st_folium(m2, use_container_width=True, height=480)

# ---------------------------------------------------------
# TAB 3: AI 보행 지원 (Gemini)
# ---------------------------------------------------------
with tab3:
    if not ai_enabled:
        st.warning("🔒 Gemini API 키가 설정되지 않았습니다. Streamlit Secrets에 `GEMINI_API_KEY`를 추가하여 AI 기능을 활성화하세요.")
    else:
        c1, c2 = st.columns(2, gap="medium")
        
        with c1:
            st.markdown("""
                <div class="custom-card">
                    <div class="card-title">💬 AI 보행 접근성 상담</div>
                </div>
            """, unsafe_allow_html=True)
            
            q = st.text_input("질문 입력", placeholder="예: 전동휠체어로 지하철 환승 시 가장 쉬운 방법은?")
            if st.button("AI 가이드 물어보기", use_container_width=True):
                if q:
                    with st.spinner("Gemini AI가 이동 접근성 정보를 분석 중입니다..."):
                        try:
                            prompt = f"""
                            당신은 장애인 보행 접근성 전문가입니다.
                            다음 문의에 대해 휠체어 이용자, 시각장애인, 노약자가 이해하기 쉬운 형태로 핵심 이동 팁을 제시하세요.
                            질문: {q}
                            """
                            res = model.generate_content(prompt)
                            st.markdown("---")
                            st.markdown("#### 🤖 AI 답변")
                            st.info(res.text)
                        except Exception as e:
                            st.error(f"오류 발생: {e}")
                else:
                    st.warning("질문을 입력해 주세요.")
                    
        with c2:
            st.markdown("""
                <div class="custom-card">
                    <div class="card-title">📷 길거리 장애물 사진 분석 (Vision)</div>
                </div>
            """, unsafe_allow_html=True)
            
            img_file = st.file_uploader("보도/장애물 사진 업로드", type=["jpg", "png", "jpeg"])
            if img_file:
                img = Image.open(img_file)
                st.image(img, caption="업로드한 이미지", use_container_width=True)
                
                if st.button("🔍 장애물 통행가능 여부 분석", use_container_width=True):
                    with st.spinner("이미지를 분석 중입니다..."):
                        try:
                            prompt = """
                            사진속 이동 경로를 분석하세요:
                            1. 휠체어/유모차 진입 가능 여부 (가능/주의/불가)
                            2. 통행을 방해하는 장애물 요소
                            3. 추천하는 회피 또는 안전 수칙
                            """
                            res = model.generate_content([prompt, img])
                            st.markdown("---")
                            st.markdown("#### 📊 분석 결과")
                            st.success(res.text)
                        except Exception as e:
                            st.error(f"분석 실패: {e}")
