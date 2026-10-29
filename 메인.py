import streamlit as st

# 1. 페이지 기본 설정 (시각 장애인을 고려한 Wide 및 대형 배치)
st.set_page_config(
    page_title="배리어프리 스마트 통합 센터",
    page_icon="♿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS로 가독성 높이기 (접근성 고려)
st.markdown("""
    <style>
    .main-header {
        font-size: 2.2rem;
        font-weight: bold;
        color: #1E88E5;
        margin-bottom: 10px;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #555555;
        margin-bottom: 25px;
    }
    .service-card {
        background-color: #F8F9FA;
        border-radius: 12px;
        padding: 20px;
        border-left: 6px solid #1E88E5;
        margin-bottom: 15px;
    }
    </style>
""", unsafe_allow_html=True)

# 메인 타이틀 및 소개
st.markdown('<div class="main-header">♿ 배리어프리 스마트 이동지원 센터</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">모든 사용자가 안전하고 편리하게 이동할 수 있도록 지원하는 통합 서비스 플랫폼입니다.</div>', unsafe_allow_html=True)

st.divider()

# 2. 메인 페이지 - 팀 기능 페이지 바로가기 (핵심 요청 기능)
st.subheader("📌 주요 기능 바로가기")
st.write("아래 원하시는 서비스를 선택하시면 해당 기능 페이지로 즉시 이동합니다.")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
        <div class="service-card">
            <h3>🧭 장애인의 내비게이션</h3>
            <p>휠체어 및 교통약자를 위한 계단 없는 길, 휠체어 리프트, 휠체어 전용 경로 안내 서비스입니다.</p>
        </div>
    """, unsafe_allow_html=True)
    # pages/장애인의 내비게이션.py 파일 연결
    try:
        st.page_link("pages/장애인의 내비게이션.py", label="👉 내비게이션 이동하기", icon="🧭", use_container_width=True)
    except Exception:
        st.warning("⚠️ 'pages/장애인의 내비게이션.py' 파일 경로를 확인해주세요.")

with col2:
    st.markdown("""
        <div class="service-card">
            <h3>💳 횡단보도 전용카드 인식기</h3>
            <p>보행 신호 연장 및 시각장애인 보행 지원 전용 카드를 인식하고 신호를 제어/안내합니다.</p>
        </div>
    """, unsafe_allow_html=True)
    # pages/횡단보도 전용카드 인식기.py 파일 연결
    try:
        st.page_link("pages/횡단보도 전용카드 인식기.py", label="👉 전용카드 인식기 이동하기", icon="💳", use_container_width=True)
    except Exception:
        st.warning("⚠️ 'pages/횡단보도 전용카드 인식기.py' 파일 경로를 확인해주세요.")

st.divider()

# 3. 메인 전용 접근성 편의 기능 (추가 제안 기능)
st.subheader("🚨 긴급 도우미 및 편의 서비스")

tab1, tab2 = st.tabs(["🆘 긴급 도우미 호출", "🔊 음성 및 대화형 접근성 가이드"])

with tab1:
    st.write("위급 상황 시 지정된 보호자 또는 긴급 구호 센터에 즉시 연락합니다.")
    emergency_type = st.radio("상황 선택", ["이동 불가능 (기계 고장/경사로 blockage)", "보행 신호 긴급 연장 필요", "기타 긴급 상황"], horizontal=True)
    
    if st.button("🚨 긴급 알림 전송", type="primary"):
        st.error(f"[{emergency_type}] 긴급 메시지가 보호자 및 스마트 보행 지원센터로 전달되었습니다.")

with tab2:
    st.write("화면 읽기 도구(스크린 리더) 사용자를 위해 텍스트 안내를 지원합니다.")
    user_text = st.text_input("음성으로 읽어줄 텍스트 입력", "배리어프리 스마트 서비스에 오신 것을 환영합니다.")
    if st.button("🔊 음성 출력 안내 시작"):
        st.info(f"🔊 읽는 중: '{user_text}'")

# 사이드바 안내
st.sidebar.title("♿ 배리어프리 안내")
st.sidebar.info(
    "왼쪽 메뉴(pages)에서도 바로 원하시는 기능 페이지로 이동하실 수 있습니다.\n\n"
    "- 장애인의 내비게이션\n"
    "- 횡단보도 전용카드 인식기"
)
