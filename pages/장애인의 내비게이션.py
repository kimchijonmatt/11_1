import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
import google.generativeai as genai
from PIL import Image
import os

# 1. 페이지 기본 설정
st.set_page_config(
    page_title="장애인을 위한 무장애 내비게이션 (Barrier-Free Nav)",
    page_icon="♿",
    layout="wide"
)

# Custom CSS for Accessibility & UI Enhancement
st.markdown("""
    <style>
    .main-title {
        font-size: 2.2rem;
        font-weight: bold;
        color: #1E88E5;
        margin-bottom: 10px;
    }
    .sub-title {
        font-size: 1.1rem;
        color: #555555;
        margin-bottom: 25px;
    }
    .stButton>button {
        width: 100%;
        font-weight: bold;
        height: 3rem;
        background-color: #1E88E5;
        color: white;
    }
    .info-card {
        background-color: #F0F4F8;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #1E88E5;
        margin-bottom: 15px;
    }
    </style>
""", unsafe_allow_html=True)

# 2. Gemini API 설정
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", None)
ai_enabled = False

if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-2.5-flash-lite')
        ai_enabled = True
    except Exception as e:
        st.error(f"Gemini API 연결 실패: {e}")

# 3. 데이터 세션 상태 초기화 (제보된 장애물 저장)
if 'reports' not in st.session_state:
    st.session_state.reports = [
        {"lat": 37.5665, "lon": 126.9780, "type": "엘리베이터 고장", "desc": "시청역 1번 출구 엘리베이터 점검 중"},
        {"lat": 37.5700, "lon": 126.9820, "type": "공사 구간", "desc": "보도블록 교체로 인해 휠체어 통행 불가"}
    ]

# 편의시설 샘플 데이터 (서울 시청 주변 예시)
FACILITIES = [
    {"name": "시청역 장애인 화장실", "lat": 37.5662, "lon": 126.9784, "category": "화장실"},
    {"name": "광화문역 전동휠체어 충전소", "lat": 37.5715, "lon": 126.9768, "category": "충전소"},
    {"name": "덕수궁 입구 경사로", "lat": 37.5658, "lon": 126.9752, "category": "경사로"},
    {"name": "서울시청 지하 휠체어 리프트", "lat": 37.5668, "lon": 126.9788, "category": "리프트"}
]

# 4. 헤더
st.markdown("<div class='main-title'>♿ 무장애 보행 내비게이션 (Barrier-Free Nav)</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-title'>휠체어, 교통약자, 시각장애인을 위한 안전하고 편리한 경로 탐색 및 AI 도우미 서비스</div>", unsafe_allow_html=True)

# 탭 구성
tab1, tab2, tab3 = st.tabs(["🗺️ 무장애 경로 탐색", "📍 편의시설 및 제보 지도", "🤖 AI 보행 및 장애물 분석"])

# ---------------------------------------------------------
# TAB 1: 무장애 경로 탐색
# ---------------------------------------------------------
with tab1:
    st.subheader("🚶‍♂️ 장애인 맞춤형 길찾기")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("<div class='info-card'><b>경로 옵션 설정</b></div>", unsafe_allow_html=True)
        start_point = st.text_input("출발지", value="서울역", help="출발 장소를 입력하세요.")
        end_point = st.text_input("목적지", value="광화문광장", help="도착 장소를 입력하세요.")
        
        user_type = st.radio(
            "이동 방식 선택",
            ["휠체어 이용자 (경사로/엘리베이터 우선)", "시각장애인 (점자블록/음향신호기 우선)", "고령자/유모차 (계단 피하기)"]
        )
        
        avoid_stairs = st.checkbox("계단 완전히 제외", value=True)
        avoid_slope = st.checkbox("급경사 구간 회피", value=True)
        
        search_btn = st.button("🚀 경로 탐색하기")
        
    with col2:
        if search_btn:
            st.success(f"**[{start_point}]** ➡️ **[{end_point}]** 추천 경로 탐색 완료!")
            
            # 경로 요약 안내
            st.info(f"💡 **선택한 조건**: {user_type} | 계단 제외: {'예' if avoid_stairs else '아니오'}")
            
            # 시뮬레이션 결과 경로 정보
            st.markdown("### 📋 추천 경로 안내")
            st.markdown("""
            1. **[출발]** 서울역 1번 출구 (엘리베이터 이용 지하 이동)
            2. **[보행]** 평지 보도 따라 300m 이동 (턱 없음, 보도폭 2.5m 이상 확보)
            3. **[횡단]** 횡단보도 이용 (음향신호기 설치 완료 구간)
            4. **[도착]** 광화문광장 지상 경사로 진입
            """)
            
            # 경로 정보 요약
            col_a, col_b, col_c = st.columns(3)
            col_a.metric("총 이동 거리", "1.8 km")
            col_b.metric("소요 시간", "약 28분")
            col_c.metric("보행 장애물", "0개 (안전)")
            
            # 지도 시각화 (서울역 - 광화문 대략적 위치)
            m = folium.Map(location=[37.5600, 126.9750], zoom_start=14)
            folium.Marker([37.5559, 126.9723], popup="출발: 서울역", icon=folium.Icon(color="green", icon="play")).add_to(m)
            folium.Marker([37.5759, 126.9768], popup="도착: 광화문광장", icon=folium.Icon(color="red", icon="flag")).add_to(m)
            
            # 추천 경로 선 그리기
            route_coords = [
                [37.5559, 126.9723],
                [37.5620, 126.9750],
                [37.5665, 126.9780],
                [37.5759, 126.9768]
            ]
            folium.PolyLine(route_coords, color="#1E88E5", weight=6, opacity=0.8, tooltip="휠체어 추천 경로").add_to(m)
            st_folium(m, width="100%", height=350)
        else:
            st.info("👈 왼쪽에서 출발지와 목적지를 입력하고 경로를 탐색해보세요.")
            # 기본 지도
            default_map = folium.Map(location=[37.5665, 126.9780], zoom_start=13)
            st_folium(default_map, width="100%", height=380)

# ---------------------------------------------------------
# TAB 2: 편의시설 및 제보 지도
# ---------------------------------------------------------
with tab2:
    st.subheader("🗺️ 주변 편의시설 및 위험 장애물 공유")
    
    col_map, col_report = st.columns([2, 1])
    
    with col_report:
        st.markdown("<div class='info-card'><b>⚠️ 실시간 장애물/불편 제보</b></div>", unsafe_allow_html=True)
        rep_type = st.selectbox("제보 유형", ["엘리베이터 고장", "공사 구간", "보도블록 파손", "경사로 막힘", "기타"])
        rep_desc = st.text_area("상세 내용", placeholder="예: 3번 출구 앞 엘리베이터 점검 중입니다.")
        rep_lat = st.number_input("위도 (Latitude)", value=37.5670, format="%.4f")
        rep_lon = st.number_input("경도 (Longitude)", value=126.9790, format="%.4f")
        
        if st.button("📢 제보 등록하기"):
            if rep_desc:
                st.session_state.reports.append({
                    "lat": rep_lat,
                    "lon": rep_lon,
                    "type": rep_type,
                    "desc": rep_desc
                })
                st.success("성공적으로 제보가 등록되었습니다!")
            else:
                st.warning("상세 내용을 입력해 주세요.")
                
    with col_map:
        st.markdown("##### 📍 시설 정보 및 제보 현황 지도")
        m2 = folium.Map(location=[37.5665, 126.9780], zoom_start=14)
        
        # 1. 편의시설 마커 추가 (파란색)
        for fac in FACILITIES:
            folium.Marker(
                [fac["lat"], fac["lon"]],
                popup=f"<b>{fac['name']}</b> ({fac['category']})",
                icon=folium.Icon(color="blue", icon="info-sign")
            ).add_to(m2)
            
        # 2. 사용자 제보 장애물 마커 추가 (빨간색)
        for rep in st.session_state.reports:
            folium.Marker(
                [rep["lat"], rep["lon"]],
                popup=f"<b>[위험] {rep['type']}</b><br>{rep['desc']}",
                icon=folium.Icon(color="red", icon="exclamation-sign")
            ).add_to(m2)
            
        st_folium(m2, width="100%", height=450)

# ---------------------------------------------------------
# TAB 3: Gemini AI 보행 및 장애물 분석
# ---------------------------------------------------------
with tab3:
    st.subheader("🤖 Gemini AI 장애인 보행 지원 도우미")
    
    if not ai_enabled:
        st.warning("⚠️ Gemini API 키가 설정되지 않았습니다. Secrets에 `GEMINI_API_KEY`를 등록하면 AI 기능을 사용할 수 있습니다.")
    else:
        col_ai1, col_ai2 = st.columns(2)
        
        # 1. 보행 관련 Q&A
        with col_ai1:
            st.markdown("<div class='info-card'><b>💬 이동 및 접근성 문의</b></div>", unsafe_allow_html=True)
            user_question = st.text_input("질문 입력", placeholder="예: 전동휠체어로 지하철 환승 시 주의사항 알려줘")
            
            if st.button("AI에게 질문하기"):
                if user_question:
                    with st.spinner("AI가 답변을 생성 중입니다..."):
                        try:
                            prompt = f"""
                            당신은 장애인 보행 및 이동 접근성 전문 AI 가이드입니다.
                            다음 질문에 대해 휠체어 이용자, 시각장애인, 노약자의 관점에서 친절하고 안전한 이동 팁을 제공해 주세요.
                            
                            질문: {user_question}
                            """
                            response = model.generate_content(prompt)
                            st.markdown("### 🤖 AI 답변")
                            st.write(response.text)
                        except Exception as e:
                            st.error(f"AI 응답 도중 오류가 발생했습니다: {e}")
                else:
                    st.warning("질문을 입력해 주세요.")
                    
        # 2. 장애물 사진 분석 (Vision)
        with col_ai2:
            st.markdown("<div class='info-card'><b>📷 길거리 장애물 사진 분석</b></div>", unsafe_allow_html=True)
            uploaded_file = st.file_uploader("장애물 또는 도로 사진 업로드", type=["jpg", "jpeg", "png"])
            
            if uploaded_file is not None:
                image = Image.open(uploaded_file)
                st.image(image, caption="업로드한 이미지", use_column_width=True)
                
                if st.button("🔍 사진 분석하기"):
                    with st.spinner("이미지를 분석하여 이동 가능 여부를 판단 중입니다..."):
                        try:
                            prompt = """
                            이 사진은 이동 약자(휠체어, 시각장애인 등)가 지나갈 도로/장애물 사진입니다.
                            다음 3가지를 분석해 주세요:
                            1. 휠체어/유모차 통행 가능 여부 (가능/불가/주의)
                            2. 발견된 주요 장애물 (예: 계단, 높은 턱, 공사 구조물, 좁은 보도)
                            3. 이동 약자를 위한 안전 행동 요령
                            """
                            response = model.generate_content([prompt, image])
                            st.markdown("### 📊 AI 사진 분석 결과")
                            st.write(response.text)
                        except Exception as e:
                            st.error(f"이미지 분석 중 오류가 발생했습니다: {e}")
