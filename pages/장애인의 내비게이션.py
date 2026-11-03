
import streamlit as st
import requests
import pydeck as pdk
import math

st.set_page_config(
    page_title="모두의 길",
    page_icon="♿",
    layout="wide"
)

st.markdown("""
<style>
.stApp {
    background: #f4f7fb;
}
.hero {
    background: linear-gradient(120deg, #123d68, #2785b8);
    padding: 30px;
    border-radius: 16px;
    color: white;
}
.hero h1 {
    color: white;
    font-size: 36px;
}
.hero p {
    color: #eaf5ff;
    font-size: 17px;
}
.card {
    background: white;
    padding: 20px;
    border-radius: 12px;
    border: 1px solid #e1e8f0;
    margin-bottom: 12px;
}
</style>
""", unsafe_allow_html=True)

HEADERS = {
    "User-Agent": "ModudeGilNavigation/1.0"
}

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

ROUTING_URL = (
    "https://routing.openstreetmap.de/"
    "routed-foot/route/v1/driving/"
)


# 장소 검색
@st.cache_data(ttl=3600)
def search_location(place):

    if not place.strip():
        raise ValueError("장소를 입력해주세요.")

    response = requests.get(
        NOMINATIM_URL,
        params={
            "q": place,
            "format": "jsonv2",
            "limit": 1,
            "accept-language": "ko"
        },
        headers=HEADERS,
        timeout=15
    )

    response.raise_for_status()

    results = response.json()

    if not results:
        raise ValueError(
            f"'{place}' 장소를 찾을 수 없습니다."
        )

    item = results[0]

    return {
        "name": item.get("display_name", place),
        "lat": float(item["lat"]),
        "lon": float(item["lon"])
    }


# 보행 경로 검색
def get_route(start, end):

    url = (
        ROUTING_URL
        + f"{start['lon']},{start['lat']};"
        + f"{end['lon']},{end['lat']}"
    )

    response = requests.get(
        url,
        params={
            "overview": "full",
            "geometries": "geojson",
            "steps": "true",
            "alternatives": "false"
        },
        headers=HEADERS,
        timeout=30
    )

    response.raise_for_status()

    data = response.json()

    if data.get("code") != "Ok":
        raise ValueError("경로를 찾을 수 없습니다.")

    if not data.get("routes"):
        raise ValueError("이동 경로가 없습니다.")

    return data["routes"][0]


# 거리 표시
def format_distance(distance):

    if distance >= 1000:
        return f"{distance / 1000:.2f} km"

    return f"{distance:.0f} m"


# 시간 표시
def format_duration(duration):

    minutes = max(1, math.ceil(duration / 60))

    hours = minutes // 60
    remain = minutes % 60

    if hours:
        return f"{hours}시간 {remain}분"

    return f"{minutes}분"


# 지도 표시
def show_map(route, start, end):

    coordinates = route["geometry"]["coordinates"]

    path_layer = pdk.Layer(
        "PathLayer",
        data=[{"path": coordinates}],
        get_path="path",
        get_color=[25, 105, 190],
        get_width=6,
        width_min_pixels=4
    )

    points = [
        {
            "position": [start["lon"], start["lat"]],
            "name": "출발지"
        },
        {
            "position": [end["lon"], end["lat"]],
            "name": "목적지"
        }
    ]

    point_layer = pdk.Layer(
        "ScatterplotLayer",
        data=points,
        get_position="position",
        get_radius=100,
        radius_min_pixels=8,
        get_fill_color=[230, 70, 60],
        pickable=True
    )

    view = pdk.ViewState(
        latitude=(start["lat"] + end["lat"]) / 2,
        longitude=(start["lon"] + end["lon"]) / 2,
        zoom=13
    )

    deck = pdk.Deck(
        layers=[path_layer, point_layer],
        initial_view_state=view,
        map_style="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
        tooltip={"text": "{name}"}
    )

    st.pydeck_chart(deck, use_container_width=True)


# 이동 안내
def get_steps(route):

    instructions = []

    for leg in route.get("legs", []):

        for step in leg.get("steps", []):

            distance = step.get("distance", 0)

            if distance < 5:
                continue

            maneuver = step.get("maneuver", {})
            action = maneuver.get("type", "")
            modifier = maneuver.get("modifier", "")
            road = step.get("name", "")

            if action == "depart":
                message = "출발하세요."

            elif action == "arrive":
                message = "목적지에 도착합니다."

            elif action == "turn":
                message = f"{modifier} 방향으로 이동하세요."

            elif action == "roundabout":
                message = "회전교차로를 통과하세요."

            else:
                message = "현재 방향으로 계속 이동하세요."

            if road:
                message += f" 도로명: {road}"

            message += f" ({format_distance(distance)})"

            instructions.append(message)

    return instructions


# 상단 화면
st.markdown("""
<div class="hero">
    <h1>♿ 모두의 길</h1>
    <p>누구나 자유롭게 이동할 수 있도록.<br>
    나에게 맞는 보행 경로를 찾아보세요.</p>
</div>
""", unsafe_allow_html=True)

# 사이드바
with st.sidebar:

    st.title("⚙️ 이동 설정")

    mobility = st.selectbox(
        "이동 유형",
        [
            "휠체어 사용자",
            "시각장애인",
            "보행 보조기구 사용자",
            "고령자",
            "일반 보행자"
        ]
    )

    st.markdown("---")
    st.subheader("접근성 조건")

    preferences = {
        "계단 주의": st.checkbox("계단이 있는 길 주의"),
        "경사로 필요": st.checkbox("경사로 필요"),
        "넓은 보행 공간": st.checkbox("넓은 보행 공간 필요"),
        "횡단보도 확인": st.checkbox("횡단보도 확인"),
        "급경사 주의": st.checkbox("급경사 주의")
    }

    st.info(
        "선택한 조건은 안전 체크리스트에 반영됩니다. "
        "실제 경로 계산에 적용되는 것은 아닙니다."
    )

# 메인 화면
st.subheader("📍 이동 경로 검색")

with st.form("navigation_form"):

    col1, col2 = st.columns(2)

    with col1:
        start_place = st.text_input(
            "🟢 출발지",
            placeholder="예: 서울역"
        )

    with col2:
        end_place = st.text_input(
            "🔴 목적지",
            placeholder="예: 서울시청"
        )

    submitted = st.form_submit_button(
        "🚀 경로 검색",
        use_container_width=True
    )


# 경로 검색 실행
if submitted:

    if not start_place.strip() or not end_place.strip():

        st.error("출발지와 목적지를 입력해주세요.")

    elif start_place.strip() == end_place.strip():

        st.warning("출발지와 목적지가 같습니다.")

    else:

        try:

            with st.spinner("경로를 검색하고 있습니다..."):

                start = search_location(start_place)
                end = search_location(end_place)

                route = get_route(start, end)

                st.session_state["result"] = {
                    "start": start,
                    "end": end,
                    "route": route,
                    "mobility": mobility,
                    "preferences": preferences
                }

        except requests.exceptions.Timeout:

            st.error("서버 응답 시간이 초과되었습니다.")

        except requests.exceptions.RequestException:

            st.error(
                "지도 서버에 연결할 수 없습니다. "
                "잠시 후 다시 시도해주세요."
            )

        except (ValueError, KeyError, TypeError) as e:

            st.error(f"검색 오류: {e}")

        except Exception:

            st.error("예상하지 못한 오류가 발생했습니다.")


# 검색 결과
if "result" in st.session_state:

    result = st.session_state["result"]

    start = result["start"]
    end = result["end"]
    route = result["route"]

    st.markdown("---")
    st.header("🗺️ 이동 경로")

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "총 이동 거리",
        format_distance(route["distance"])
    )

    col2.metric(
        "예상 이동 시간",
        format_duration(route["duration"])
    )

    col3.metric(
        "이동 유형",
        result["mobility"]
    )

    st.markdown("### 출발지와 목적지")

    st.write("🟢 출발지:", start["name"])
    st.write("🔴 목적지:", end["name"])

    st.markdown("### 지도")

    show_map(route, start, end)

    st.caption(
        "파란색 선은 보행 라우팅 엔진의 경로입니다. "
        "실제 접근성이나 안전을 보장하지 않습니다."
    )

    st.markdown("---")
    st.header("🚶 이동 안내")

    instructions = get_steps(route)

    if instructions:

        for i, instruction in enumerate(instructions):

            st.markdown(
                f"""
                <div class="card">
                    <b>{i + 1}.</b> {instruction}
                </div>
                """,
                unsafe_allow_html=True
            )

    else:

        st.info("상세 이동 안내가 없습니다.")

    st.markdown("---")
    st.header("♿ 접근성 체크리스트")

    for key, enabled in result["preferences"].items():

        if enabled:
            st.warning(f"⚠️ {key}: 이동 전 현장 확인이 필요합니다.")
        else:
            st.write(f"☑️ {key}")

    st.markdown("---")
    st.header("💡 이동 안전 안내")

    safety_messages = {
        "휠체어 사용자": [
            "보도 턱과 단차를 확인하세요.",
            "경사로의 기울기와 폭을 확인하세요.",
            "휠체어 통행 공간을 확인하세요."
        ],
        "시각장애인": [
            "점자블록을 확인하세요.",
            "음향 신호기의 작동 여부를 확인하세요.",
            "공사 구간과 장애물을 주의하세요."
        ],
        "보행 보조기구 사용자": [
            "바닥의 미끄러움을 확인하세요.",
            "휴식 공간을 미리 확인하세요.",
            "급경사 구간을 주의하세요."
        ],
        "고령자": [
            "충분한 휴식 시간을 확보하세요.",
            "보행로의 단차를 확인하세요.",
            "횡단보도 신호 시간을 확인하세요."
        ],
        "일반 보행자": [
            "주변 교통 상황을 확인하세요.",
            "공사 구간에 주의하세요.",
            "횡단보도 신호를 준수하세요."
        ]
    }

    for message in safety_messages[result["mobility"]]:
        st.write(f"- {message}")

    st.warning(
        "주의: 이 앱은 보행 경로 참고용입니다. "
        "계단, 경사도, 점자블록, 엘리베이터 등의 "
        "실제 접근성을 검증하지 않습니다. "
        "이동 전 현장 상황을 반드시 확인하세요."
    )

else:

    st.markdown("---")
    st.header("🌈 모두를 위한 이동")

    col1, col2 = st.columns(2)

    with col1:

        st.markdown("""
        <div class="card">
            <h3>♿ 휠체어 사용자</h3>
            <p>보도 턱과 경사로를 이동 전 확인하세요.</p>
        </div>
        <div class="card">
            <h3>👴 고령자</h3>
            <p>보행 안전과 휴식 공간을 확인하세요.</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:

        st.markdown("""
        <div class="card">
            <h3>🦯 시각장애인</h3>
            <p>점자블록과 음향 신호기를 확인하세요.</p>
        </div>
        <div class="card">
            <h3>🦽 보행 보조기구 사용자</h3>
            <p>노면 상태와 장애물에 주의하세요.</p>
        </div>
        """, unsafe_allow_html=True)

    st.info(
        "왼쪽 메뉴에서 이동 유형을 선택하고 "
        "출발지와 목적지를 입력해보세요!"
    )

st.markdown("---")

st.caption(
    "모두의 길 | OpenStreetMap 기반 이동 지원 서비스"
)
