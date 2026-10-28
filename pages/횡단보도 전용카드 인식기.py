
import streamlit as st
import csv
import io
import math
import struct
import wave
from datetime import datetime

st.set_page_config(
    page_title="함께 걷는 횡단보도",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- 화면 디자인 ----------
st.markdown(
    """
    <style>
    .stApp {
        background-color: #F4F8FC;
    }
    .block-container {
        max-width: 1100px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }
    h1, h2, h3, p, label {
        color: #17324D;
    }
    div.stButton > button,
    div.stDownloadButton > button {
        min-height: 48px;
        font-weight: 700;
        border-radius: 10px;
    }
    div[data-testid="stMetric"] {
        background: white;
        border: 1px solid #D8E3EF;
        border-radius: 12px;
        padding: 16px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- 세션 데이터 ----------
if "history" not in st.session_state:
    st.session_state.history = []

if "current_request" not in st.session_state:
    st.session_state.current_request = None


def make_beep():
    """외부 오디오 파일 없이 테스트용 알림음을 생성합니다."""
    sample_rate = 22050
    duration = 0.35
    frequency = 880
    volume = 0.35
    frames = bytearray()

    for i in range(int(sample_rate * duration)):
        fade = min(1.0, i / 300, (sample_rate * duration - i) / 300)
        sample = int(
            32767
            * volume
            * max(0, fade)
            * math.sin(2 * math.pi * frequency * i / sample_rate)
        )
        frames.extend(struct.pack("<h", sample))

    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(sample_rate)
        audio.writeframes(bytes(frames))

    return buffer.getvalue()


def add_history(card_id, extension, audio, status):
    """현재 세션에 요청 기록을 추가합니다."""
    now = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
    st.session_state.history.insert(
        0,
        {
            "시간": now,
            "카드번호": card_id,
            "보행시간연장요청": "예" if extension else "아니오",
            "안내음요청": "예" if audio else "아니오",
            "상태": status,
        },
    )


# ---------- 제목 ----------
st.title("🚦 함께 걷는 횡단보도")
st.markdown(
    "장애인과 보행 약자를 위한 **보행 지원 카드 입력 시제품**입니다."
)

st.warning(
    "시제품 안내: 이 앱은 실제 교통신호기를 제어하지 않습니다. "
    "시간 연장과 안내음은 테스트 요청이며, 실제 도로에 적용하려면 "
    "승인된 교통신호 제어 장치와의 연동이 필요합니다."
)

# ---------- 사이드바 ----------
with st.sidebar:
    st.header("⚙️ 지원 설정")
    st.caption("테스트 요청에 적용할 지원 기능을 선택하세요.")

    extension_seconds = st.select_slider(
        "요청할 추가 보행 시간(초)",
        options=[5, 10, 15, 20, 30, 45, 60],
        value=15,
    )

    st.info(
        "선택한 시간은 요청값일 뿐입니다. "
        "실제 횡단보도 신호 시간이 변경되는 것은 아닙니다."
    )

    st.divider()
    st.subheader("사용 방법")
    st.markdown(
        """
        1. 테스트 카드 번호를 입력합니다.
        2. 필요한 지원 기능을 선택합니다.
        3. **카드 인식 및 요청** 버튼을 누릅니다.
        4. 결과와 요청 기록을 확인합니다.
        """
    )

# ---------- 상단 현황 ----------
history = st.session_state.history
total_requests = len(history)
extension_count = sum(
    row["보행시간연장요청"] == "예" for row in history
)
audio_count = sum(row["안내음요청"] == "예" for row in history)

col1, col2, col3 = st.columns(3)
col1.metric("전체 요청", f"{total_requests}건")
col2.metric("시간 연장 요청", f"{extension_count}건")
col3.metric("안내음 요청", f"{audio_count}건")

st.divider()

# ---------- 카드 입력 ----------
st.header("💳 보행 지원 카드 입력")

st.caption(
    "실제 카드 리더기가 없어도 테스트할 수 있도록 "
    "키보드 입력 방식을 사용합니다."
)

with st.form("card_form"):
    card_id = st.text_input(
        "카드 식별번호",
        placeholder="예: TEST-0001",
        help="개인정보가 아닌 테스트용 식별번호 사용을 권장합니다.",
        max_chars=40,
    )

    demo_col1, demo_col2 = st.columns(2)

    with demo_col1:
        request_extension = st.checkbox(
            "보행 시간 연장 요청",
            value=True,
        )

    with demo_col2:
        request_audio = st.checkbox(
            "안내음 재생 요청",
            value=True,
        )

    submitted = st.form_submit_button(
        "카드 인식 및 요청",
        type="primary",
        use_container_width=True,
    )

if submitted:
    cleaned_card_id = card_id.strip()

    if not cleaned_card_id:
        st.error("카드 식별번호를 입력해 주세요.")
    elif not request_extension and not request_audio:
        st.error("최소 하나의 지원 기능을 선택해 주세요.")
    else:
        status = "시제품에서 요청 접수"

        st.session_state.current_request = {
            "card_id": cleaned_card_id,
            "extension": request_extension,
            "extension_seconds": (
                extension_seconds if request_extension else 0
            ),
            "audio": request_audio,
            "time": datetime.now().astimezone().strftime(
                "%Y-%m-%d %H:%M:%S %Z"
            ),
            "status": status,
        }

        add_history(
            cleaned_card_id,
            request_extension,
            request_audio,
            status,
        )

# ---------- 요청 결과 ----------
current = st.session_state.current_request

if current:
    st.divider()
    st.header("📋 최근 요청 결과")

    st.success("카드 입력을 확인했습니다. 시제품 요청을 접수했습니다.")

    st.markdown(f"**카드 식별번호:** `{current['card_id']}`")
    st.markdown(f"**접수 시각:** {current['time']}")

    result_col1, result_col2 = st.columns(2)

    with result_col1:
        if current["extension"]:
            st.subheader("⏱️ 보행 시간 연장")
            st.metric(
                "요청 추가 시간",
                f"{current['extension_seconds']}초",
            )
            st.info(
                "연장 요청이 시제품에 기록되었습니다. "
                "실제 신호 시간은 변경되지 않았습니다."
            )
        else:
            st.subheader("⏱️ 보행 시간 연장")
            st.write("연장 요청을 선택하지 않았습니다.")

    with result_col2:
        st.subheader("🔊 안내음")
        if current["audio"]:
            st.write("안내음 재생 요청이 접수되었습니다.")
            st.audio(make_beep(), format="audio/wav")
            st.caption(
                "위 재생 버튼을 누르면 테스트용 알림음이 들립니다. "
                "브라우저 정책상 자동 재생은 보장되지 않습니다."
            )
        else:
            st.write("안내음 요청을 선택하지 않았습니다.")

    st.info(
        "보행자 안내 예시: "
        "보행 지원 요청이 접수되었습니다. "
        "주변을 확인하고 안전하게 이동해 주세요."
    )

# ---------- 기록 및 CSV ----------
st.divider()
st.header("🗂️ 요청 기록")

if st.session_state.history:
    st.caption(
        "기록은 현재 앱 세션에만 보관됩니다. "
        "앱이 재시작되면 초기화될 수 있습니다."
    )

    st.dataframe(
        st.session_state.history,
        use_container_width=True,
        hide_index=True,
    )

    csv_buffer = io.StringIO()
    fieldnames = [
        "시간",
        "카드번호",
        "보행시간연장요청",
        "안내음요청",
        "상태",
    ]

    writer = csv.DictWriter(
        csv_buffer,
        fieldnames=fieldnames,
        extrasaction="ignore",
    )
    writer.writeheader()
    writer.writerows(reversed(st.session_state.history))

    st.download_button(
        "📥 요청 기록 CSV 다운로드",
        data=("\ufeff" + csv_buffer.getvalue()).encode("utf-8"),
        file_name="crosswalk_requests.csv",
        mime="text/csv",
        use_container_width=True,
    )

    if st.button("기록 초기화", type="secondary"):
        st.session_state.history = []
        st.session_state.current_request = None
        st.rerun()
else:
    st.info("아직 요청 기록이 없습니다. 테스트 카드를 입력해 보세요.")

# ---------- 하단 안내 ----------
st.divider()
st.caption(
    "함께 걷는 횡단보도 | 접근성 지원 기술 시제품 | "
    "실제 교통신호 제어 기능 미포함"
)

