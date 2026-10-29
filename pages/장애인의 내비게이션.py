import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
import google.generativeai as genai
from PIL import Image

# 1. 페이지 설정
st.set_page_config(
    page_title="Barrier-Free Nav | 무장애 길안내 서비스",
    page_icon="♿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. 고대비 & 접근성 중심 커스텀 CSS
st.markdown("""
    <style>
    /* 메인 배경 및 폰트 설정 */
    .stApp {
        background-color: #F8F9FA;
    }
    
    /* 타이틀 및 헤더 스타일 */
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
    
    /* 카드 컴포넌트 */
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

    /* 탭 디자인 강화 */
    .stTabs [data-baseweb="tab-list"] {
        gap
