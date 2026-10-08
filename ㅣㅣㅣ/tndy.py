import streamlit as st
import pandas as pd
import numpy as np
import datetime
import time

# 1. 페이지 기본 설정
st.set_page_config(
    page_title="교실 환경 & 청정도 모니터링 SYSTEM",
    page_icon="🏫",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .badge-previous {
        background-color: #6c757d;
        color: white;
        padding: 4px 10px;
        border-radius: 4px;
        font-size: 0.85rem;
        font-weight: bold;
    }
    .timer-card {
        background-color: #f0f2f6;
        border-radius: 8px;
        padding: 12px;
        text-align: center;
        margin-bottom: 10px;
    }
    .alert-banner {
        background-color: #ff3333;
        color: white;
        padding: 20px;
        border-radius: 12px;
        text-align: center;
        font-size: 1.5rem;
        font-weight: bold;
        box-shadow: 0 4px 12px rgba(255,51,51,0.3);
        margin-bottom: 25px;
        animation: pulse 1.5s infinite;
    }
    .ai-coaching-card {
        background-color: #eef2ff;
        border-left: 6px solid #4f46e5;
        padding: 16px;
        border-radius: 8px;
        margin-top: 15px;
        margin-bottom: 15px;
    }
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.01); }
        100% { transform: scale(1); }
    }
</style>
""", unsafe_allow_html=True)

# 브라우저 효과음 재생 함수 (Web Audio API)
def play_alarm_sound():
    sound_script = """
    <script>
    (function() {
        try {
            var ctx = new (window.AudioContext || window.webkitAudioContext)();
            function playBeep(freq, delay, duration) {
                setTimeout(function() {
                    var osc = ctx.createOscillator();
                    var gain = ctx.createGain();
                    osc.type = 'sine';
                    osc.frequency.value = freq;
                    gain.gain.setValueAtTime(0.3, ctx.currentTime);
                    osc.connect(gain);
                    gain.connect(ctx.destination);
                    osc.start();
                    osc.stop(ctx.currentTime + duration);
                }, delay);
            }
            playBeep(880, 0, 0.2);
            playBeep(880, 300, 0.2);
            playBeep(880, 600, 0.4);
        } catch(e) {
            console.log("Audio play blocked by browser policy");
        }
    })();
    </script>
    """
    st.components.v1.html(sound_script, height=0)

# 2. 각 요소별 설명 텍스트
HELP_TEXTS = {
    "temp": "🌡️ 온도 (℃)\n- 교실 내부 기온\n- 쾌적한 학습 환경 유지 및 적정 실내 온도 관리 (적정: 18~22℃)",
    "humidity": "💧 습도 (%)\n- 공기 중 수증기 비율\n- 정전기 방지 및 바이러스 활성화 억제 (적정: 40~60%)",
    "pm25": "🌫️ 초미세먼지 PM2.5 (µg/m³)\n- 지름 2.5µm 이하의 미세 입자 농도\n- 학생들의 호흡기 건강 보호 및 공기질 판단 기준 (권장: 35µg/m³ 이하)",
    "co2": "🫧 CO₂ 농도 (ppm)\n- 공기 중 이산화탄소 비율\n- 환기 부족 시 상승하며 집중력 저하 및 졸음 유발 (권장: 1,000ppm 이하)",
    "lux": "💡 조도 (Lux)\n- 교실 내부 밝기\n- 시력 보호 및 학습 집중도를 위한 밝기 상태 (권장: 300~700 Lux)",
    "clean_class": "🏷️ 공정 청정도 등급 (Clean Class)\n- 단위 부피당 미세입자 수 기준\n- Class 100: 매우 좋음 | Class 1,000: 보통 | Class 10,000: 환기 필요"
}

# 3. 청정도 등급 판정 함수
def evaluate_cleanliness(pm25):
    if pm25 <= 15.0:
        return "Class 100 (매우 좋음)"
    elif pm25 <= 35.0:
        return "Class 1,000 (보통)"
    else:
        return "Class 10,000 (주의)"

# 4. 학습 쾌적도 지수(0~100점) 계산 함수
def calculate_comfort_score(temp, humidity, co2, pm25):
    score = 100
    if temp < 18 or temp > 22:
        score -= min(20, abs(temp - 20) * 3)
    if humidity < 40 or humidity > 60:
        score -= min(15, abs(humidity - 50) * 0.5)
    if co2 > 1000:
        score -= min(35, (co2 - 1000) / 30)
    if pm25 > 35:
        score -= min(30, (pm25 - 35) * 1.5)
        
    final_score = int(max(0, score))
    if final_score >= 85:
        status = "😊 최적 (학습 환경 매우 쾌적)"
    elif final_score >= 70:
        status = "😐 보통 (일부 요소 관리가 필요함)"
    elif final_score >= 50:
        status = "😷 주의 (환기 및 환경 조치 필요)"
    else:
        status = "🚨 경고 (학습 효율 저하 위험, 즉시 환기!)"
        
    return final_score, status

# AI 맞춤형 환경 코칭 메시지 생성 함수
def generate_ai_coaching(temp, humidity, co2, pm25, lux):
    coaching_list = []
    
    if co2 > 1000 and temp < 18:
        coaching_list.append("❄️ **복합 코칭**: 실내 이산화탄소가 높아 환기가 필요한데 실외 기온이 낮습니다. 창문을 전체 다 열지 말고, **앞·뒷문 위쪽 창문만 5분간 짧게 열어 겉옷을 입고 맞통풍 환기**를 실시하세요.")
    elif co2 > 1000 and pm25 > 35:
        coaching_list.append("🌫️ **복합 코칭**: CO₂와 외부 미세먼지가 동시에 높습니다. 창문을 여는 것보다 **복도 쪽 문을 열고 공기청정기를 최고 풍량(터보 모드)으로 동시에 가동**하세요.")
    elif co2 > 1000:
        coaching_list.append("🌬️ **환기 코칭**: CO₂ 농도가 높아 집중력이 저하될 수 있습니다. **창문과 교실 문을 동시에 10분간 활짝 열어주세요.**")
        
    if humidity < 40:
        coaching_list.append("💧 **습도 코칭**: 공기가 건조해 바이러스 활동이 활발해질 수 있습니다. **가습기를 틀거나 교실 내 미니 식물/젖은 수건을 활용**하세요.")
    elif humidity > 60:
        coaching_list.append("☂️ **습도 코칭**: 실내 습도가 높아 불쾌지수가 상승할 수 있습니다. **제습 모드 가동 또는 환기**를 권장합니다.")

    if lux < 300:
        coaching_list.append("💡 **조도 코칭**: 교실 내부가 다소 어둡습니다. **눈의 피로를 줄이기 위해 전체 형광등/LED 조명을 점등**해 주세요.")

    if not coaching_list:
        return "🤖 **AI 코칭 종합**: 현재 교실의 온도, 습도, 공기질, 조도가 모두 최적의 균형을 유지하고 있습니다. 이 상태를 유지하며 수업을 진행하세요!"
    else:
        return "🤖 **AI 실시간 맞춤형 코칭 가이드**:\n\n" + "\n\n".join(coaching_list)

# HTML 정식 환경 보고서 파일 생성 함수
def generate_html_report(df, score, status_text):
    avg_temp = round(df["온도(℃)"].mean(), 1) if len(df) > 0 else 0
    avg_hum = round(df["습도(%)"].mean(), 1) if len(df) > 0 else 0
    avg_pm25 = round(df["초미세먼지(µg/m³)"].mean(), 1) if len(df) > 0 else 0
    avg_co2 = int(df["CO2(ppm)"].mean()) if len(df) > 0 else 0
    avg_lux = int(df["조도(Lux)"].mean()) if len(df) > 0 else 0
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>교실 실내 환경 모니터링 종합 보고서</title>
        <style>
            body {{ font-family: 'Malgun Gothic', sans-serif; margin: 30px; line-height: 1.6; color: #333; }}
            h1 {{ color: #1e88e5; border-bottom: 2px solid #1e88e5; padding-bottom: 10px; }}
            .summary-box {{ background-color: #f8f9fa; border-left: 5px solid #1e88e5; padding: 15px; margin: 20px 0; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th, td {{ border: 1px solid #ddd; padding: 10px; text-align: center; }}
            th {{ background-color: #1e88e5; color: white; }}
            tr:nth-child(even) {{ background-color: #f2f2f2; }}
        </style>
    </head>
    <body>
        <h1>🏫 교실 실내 환경 모니터링 종합 보고서</h1>
        <p><b>발행 시각:</b> {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <div class="summary-box">
            <h2>📌 종합 평가 요약</h2>
            <p><b>현재 학습 쾌적도 지수:</b> <span style="font-size: 1.3rem; color: #1e88e5;"><b>{score} / 100점</b></span> ({status_text})</p>
            <ul>
                <li><b>평균 실내 온도:</b> {avg_temp} ℃ (적정: 18~22℃)</li>
                <li><b>평균 실내 습도:</b> {avg_hum} % (적정: 40~60%)</li>
                <li><b>평균 초미세먼지:</b> {avg_pm25} µg/m³ (권장: 35µg/m³ 이하)</li>
                <li><b>평균 CO₂ 농도:</b> {avg_co2} ppm (권장: 1,000ppm 이하)</li>
                <li><b>평균 실내 조도:</b> {avg_lux} Lux (권장: 300~700 Lux)</li>
            </ul>
        </div>

        <h2>📋 세부 측정 데이터 기록 (최근 20건)</h2>
        {df.to_html(index=False, classes='table')}
        
        <br><br>
        <p style="text-align: center; color: #777;">본 보고서는 교실 환경 & 청정도 실시간 모니터링 SYSTEM에 의해 자동 생성되었습니다.</p>
    </body>
    </html>
    """
    return html_content

# 5. Session State 초기화
if "history" not in st.session_state:
    st.session_state.history = pd.DataFrame(columns=[
        "시간", "온도(℃)", "습도(%)", "초미세먼지(µg/m³)", "CO2(ppm)", "조도(Lux)", "청정도 등급"
    ])

if "timer_remaining" not in st.session_state:
    st.session_state.timer_remaining = 50 * 60
if "timer_active" not in st.session_state:
    st.session_state.timer_active = False
if "timer_mode_name" not in st.session_state:
    st.session_state.timer_mode_name = "📖 수업 시간"
if "timer_finished" not in st.session_state:
    st.session_state.timer_finished = False

if "lesson_scores" not in st.session_state:
    st.session_state.lesson_scores = []
if "mission_result" not in st.session_state:
    st.session_state.mission_result = None

# 6. 사이드바 - 제어 및 설정
st.sidebar.title("⚙️ 시스템 설정 및 제어")
st.sidebar.markdown("---")

data_mode = st.sidebar.radio(
    "📥 데이터 입력 방식",
    options=["실시간 자동 시뮬레이션", "사용자 수동 직접 입력"],
    help="수동 입력 선택 시 각 요소별 측정값을 직접 입력할 수 있습니다."
)

st.sidebar.markdown("---")

# 📌 1초 독립 카운트다운 타이머 프래그먼트
@st.fragment(run_every=1)
def render_timer_fragment():
    st.sidebar.subheader("⏱️ 50분 수업 / 10분 환기 타이머")

    col_btn1, col_btn2 = st.sidebar.columns(2)
    with col_btn1:
        if st.button("▶️ 수업(50분)"):
            st.session_state.timer_remaining = 50 * 60
            st.session_state.timer_active = True
            st.session_state.timer_finished = False
            st.session_state.timer_mode_name = "📖 수업 시간"
            st.session_state.lesson_scores = []
            st.session_state.mission_result = None
    with col_btn2:
        if st.button("🌬️ 환기(10분)"):
            st.session_state.timer_remaining = 10 * 60
            st.session_state.timer_active = True
            st.session_state.timer_finished = False
            st.session_state.timer_mode_name = "🌬️ 환기 시간"
            st.session_state.mission_result = None

    col_btn3, col_btn4, col_btn5 = st.sidebar.columns(3)
    with col_btn3:
        if st.button("⏸️ 일시정지"):
            st.session_state.timer_active = not st.session_state.timer_active
    with col_btn4:
        if st.button("🔄 초기화"):
            st.session_state.timer_remaining = 50 * 60
            st.session_state.timer_active = False
            st.session_state.timer_finished = False
            st.session_state.timer_mode_name = "📖 수업 시간"
            st.session_state.lesson_scores = []
            st.session_state.mission_result = None
    with col_btn5:
        if st.button("⏭️ 즉시 종료"):
            st.session_state.timer_remaining = 0
            st.session_state.timer_active = False

    if st.session_state.timer_active and st.session_state.timer_remaining > 0:
        st.session_state.timer_remaining -= 1

    if st.session_state.timer_remaining == 0 and not st.session_state.timer_finished:
        st.session_state.timer_active = False
        st.session_state.timer_finished = True
        
        if st.session_state.timer_mode_name == "📖 수업 시간":
            if len(st.session_state.lesson_scores) > 0:
                avg_score = sum(st.session_state.lesson_scores) / len(st.session_state.lesson_scores)
            else:
                avg_score = 0
            
            target = st.session_state.get("target_score", 85)
            if avg_score >= target:
                st.session_state.mission_result = {
                    "success": True,
                    "avg_score": round(avg_score, 1),
                    "msg": f"🎉 **수업 미션 성공!** (수업 평균 쾌적도: {round(avg_score, 1)}점 / 목표: {target}점 이상)"
                }
            else:
                st.session_state.mission_result = {
                    "success": False,
                    "avg_score": round(avg_score, 1),
                    "msg": f"❌ **수업 미션 실패!** (수업 평균 쾌적도: {round(avg_score, 1)}점 / 목표: {target}점 미달)"
                }

    mins, secs = divmod(st.session_state.timer_remaining, 60)
    time_display = f"{mins:02d}:{secs:02d}"

    st.sidebar.markdown(f"""
    <div class="timer-card">
        <div style="font-size: 0.9rem; color: #555;">현재 상태: <b>{st.session_state.timer_mode_name}</b></div>
        <div style="font-size: 2.2rem; font-weight: bold; color: #1e88e5;">{time_display}</div>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.timer_finished:
        st.sidebar.error("🚨 설정한 시간이 완료되었습니다!")

render_timer_fragment()

st.sidebar.markdown("---")

# 🎯 목표 쾌적도 설정
st.sidebar.subheader("🎯 수업 목표 쾌적도 설정")
target_score = st.sidebar.slider("목표 평균 쾌적도 점수 (점)", 50, 100, 85, 5)
st.session_state.target_score = target_score

st.sidebar.markdown("---")
st.sidebar.subheader("🚨 안전 임계값 (Warning Criteria)")
max_temp = st.sidebar.slider("최대 허용 온도 (℃)", 20.0, 30.0, 25.0)
max_pm25 = st.sidebar.slider("최대 허용 미세먼지 (µg/m³)", 10.0, 50.0, 35.0)
max_co2 = st.sidebar.slider("최대 허용 CO₂ (ppm)", 500, 2000, 1000)

st.sidebar.markdown("---")

# -------------------------------------------------------------
# [개선] 자동 갱신 주기를 초 단위에서 분(Minute) 단위로 변경
# -------------------------------------------------------------
if data_mode == "실시간 자동 시뮬레이션":
    st.sidebar.subheader("🔄 자동 갱신 설정")
    auto_refresh = st.sidebar.checkbox("실시간 데이터 자동 갱신 사용", value=True)
    
    refresh_interval_min = st.sidebar.slider(
        "갱신 주기 설정 (분 단위)",
        min_value=1,
        max_value=10,
        value=1,
        step=1,
        help="주기를 분 단위로 설정하면 차트 렌더링 시 발생하는 잔상 현상을 차단할 수 있습니다."
    )
    
    # 분 단위를 초(seconds)로 변환
    refresh_interval = refresh_interval_min * 60
    
    st.sidebar.caption(
        f"💡 **현재 설정**: 매 **{refresh_interval_min}분({refresh_interval}초)**마다 대시보드가 자동으로 갱신됩니다. "
        "분 단위 설정 시 화면 깜빡임과 차트 잔상 없이 깔끔하게 모니터링할 수 있습니다."
    )
else:
    auto_refresh = False
    refresh_interval = 60

if data_mode == "사용자 수동 직접 입력":
    st.sidebar.markdown("---")
    st.sidebar.subheader("📝 각 요소별 수치 직접 입력")
    
    st.sidebar.info("""
    🔍 **수치 확인 위치**
    * **온습도**: 교실 벽면 온습도계
    * **미세먼지**: 공기청정기 디스플레이
    * **CO₂**: 실내 대기질 복합 측정기
    * **조도**: 조도계 또는 측정 앱
    """)
    
    input_temp = st.sidebar.number_input("온도 (℃)", -10.0, 50.0, 22.0, 0.1, help=HELP_TEXTS["temp"])
    input_humidity = st.sidebar.number_input("습도 (%)", 0.0, 100.0, 50.0, 0.5, help=HELP_TEXTS["humidity"])
    input_pm25 = st.sidebar.number_input("초미세먼지 PM2.5 (µg/m³)", 0.0, 300.0, 12.0, 1.0, help=HELP_TEXTS["pm25"])
    input_co2 = st.sidebar.number_input("CO₂ 농도 (ppm)", 0, 5000, 650, 10, help=HELP_TEXTS["co2"])
    input_lux = st.sidebar.number_input("조도 (Lux)", 0, 2000, 500, 10, help=HELP_TEXTS["lux"])

    if len(st.session_state.history) == 0:
        now_str = datetime.datetime.now().strftime("%H:%M:%S")
        init_row = pd.DataFrame([{
            "시간": now_str, "온도(℃)": input_temp, "습도(%)": input_humidity,
            "초미세먼지(µg/m³)": input_pm25, "CO2(ppm)": input_co2, "조도(Lux)": input_lux,
            "청정도 등급": evaluate_cleanliness(input_pm25)
        }])
        st.session_state.history = init_row

# 7. 메인 화면
st.title("🏫 교실 환경 & 청정도 실시간 모니터링")
st.caption(f"현재 입력 모드: **[{data_mode}]** | 각 항목의 물음표(❓) 마우스 호버 시 의미 확인 가능")

if st.session_state.timer_finished:
    st.markdown(f"""
    <div class="alert-banner">
        🔔 [알람] {st.session_state.timer_mode_name} 종료!<br>
        <span style="font-size: 1.1rem; font-weight: normal;">교실 문과 창문을 열고 10분간 맞통풍 환기를 실시해 주세요!</span>
    </div>
    """, unsafe_allow_html=True)
    play_alarm_sound()

st.divider()

if data_mode == "사용자 수동 직접 입력":
    if st.sidebar.button("📥 현재 입력값 기록에 추가하기", type="primary"):
        now_str = datetime.datetime.now().strftime("%H:%M:%S")
        new_row = pd.DataFrame([{
            "시간": now_str, "온도(℃)": input_temp, "습도(%)": input_humidity,
            "초미세먼지(µg/m³)": input_pm25, "CO2(ppm)": input_co2, "조도(Lux)": input_lux,
            "청정도 등급": evaluate_cleanliness(input_pm25)
        }])
        st.session_state.history = pd.concat([st.session_state.history, new_row], ignore_index=True).tail(20)
        st.sidebar.success("새 측정 수치가 추가되었습니다.")

# 8. 독립 대시보드 자동 갱신 (분 단위 연동)
@st.fragment(run_every=refresh_interval if auto_refresh else None)
def render_dashboard_fragment():
    now_str = datetime.datetime.now().strftime("%H:%M:%S")

    if data_mode == "사용자 수동 직접 입력":
        current_data = {
            "timestamp": now_str, "temp": input_temp, "humidity": input_humidity,
            "pm25": input_pm25, "co2": input_co2, "lux": input_lux,
            "clean_class": evaluate_cleanliness(input_pm25)
        }
    else:
        current_data = {
            "timestamp": now_str,
            "temp": round(np.random.uniform(18.0, 28.0), 1),
            "humidity": round(np.random.uniform(35.0, 65.0), 1),
            "pm25": round(np.random.uniform(5.0, 45.0), 1),
            "co2": int(np.random.uniform(400, 1100)),
            "lux": int(np.random.uniform(300, 650)),
            "clean_class": evaluate_cleanliness(round(np.random.uniform(5.0, 45.0), 1))
        }
        
        new_row = pd.DataFrame([{
            "시간": current_data["timestamp"], "온도(℃)": current_data["temp"], "습도(%)": current_data["humidity"],
            "초미세먼지(µg/m³)": current_data["pm25"], "CO2(ppm)": current_data["co2"], "조도(Lux)": current_data["lux"],
            "청정도 등급": current_data["clean_class"]
        }])
        st.session_state.history = pd.concat([st.session_state.history, new_row], ignore_index=True).tail(20)

    score, status_text = calculate_comfort_score(
        current_data["temp"], current_data["humidity"], current_data["co2"], current_data["pm25"]
    )

    if st.session_state.timer_active and st.session_state.timer_mode_name == "📖 수업 시간":
        st.session_state.lesson_scores.append(score)

    st.subheader("📊 현재 교실 학습 쾌적도 지수 & 50분 수업 미션")
    col_s1, col_s2, col_s3 = st.columns([1.5, 3, 2])
    
    with col_s1:
        st.metric(label="현재 순간 쾌적도", value=f"{score} / 100점")
        
    with col_s2:
        st.progress(score / 100)
        st.markdown(f"**상태**: {status_text}")
        
    with col_s3:
        if st.session_state.mission_result is not None:
            if st.session_state.mission_result["success"]:
                st.success(st.session_state.mission_result["msg"])
            else:
                st.error(st.session_state.mission_result["msg"])
        elif st.session_state.timer_active and st.session_state.timer_mode_name == "📖 수업 시간":
            current_avg = round(sum(st.session_state.lesson_scores) / len(st.session_state.lesson_scores), 1) if len(st.session_state.lesson_scores) > 0 else score
            st.info(f"📖 **수업 진행 중**\n- 현재 수업 누적 평균: **{current_avg}점**\n- 목표 점수: **{target_score}점 이상**")
        else:
            st.warning("⏱️ 사이드바에서 **[▶️ 수업(50분)]** 버튼을 누르면 미션 측정이 시작됩니다.")

    st.divider()

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("🌡️ 온도", f"{current_data['temp']} ℃", help=HELP_TEXTS["temp"])
    with col2:
        st.metric("💧 습도", f"{current_data['humidity']} %", help=HELP_TEXTS["humidity"])
    with col3:
        st.metric("🌫️ 초미세먼지", f"{current_data['pm25']} µg/m³", help=HELP_TEXTS["pm25"])
    with col4:
        st.metric("🫧 CO₂ 농도", f"{current_data['co2']} ppm", help=HELP_TEXTS["co2"])
    with col5:
        st.metric("🏷️ 공정 청정도", current_data["clean_class"], help=HELP_TEXTS["clean_class"])

    ai_guide = generate_ai_coaching(
        current_data["temp"], current_data["humidity"], current_data["co2"], current_data["pm25"], current_data["lux"]
    )
    st.markdown(f"""
    <div class="ai-coaching-card">
        {ai_guide}
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    warnings, actions = [], []
    if current_data["temp"] > max_temp:
        warnings.append(f"⚠️ **온도 초과 경고**: 현재 측정 온도({current_data['temp']}℃)가 임계값({max_temp}℃)을 초과했습니다!")
        actions.append("🌡️ **온도 조절**: 냉방 장치를 가동하거나 블라인드를 내려 직사광선을 차단해 주세요.")
    if current_data["pm25"] > max_pm25:
        warnings.append(f"🚨 **미세먼지 초과 경고**: PM2.5 수치({current_data['pm25']}µg/m³)가 임계값({max_pm25}µg/m³)을 초과했습니다!")
        actions.append("🌫️ **공기 정화**: 교실 공기청정기를 강풍/터보 모드로 가동하고 환기를 고려하세요.")
    if current_data["co2"] > max_co2:
        warnings.append(f"🌬️ **CO₂ 초과 경고**: 이산화탄소 농도({current_data['co2']}ppm)가 임계값({max_co2}ppm)을 초과했습니다.")
        actions.append("🫧 **이산화탄소 환기**: 교실 앞·뒷문과 창문을 10분 이상 열어 환기하세요.")
    if current_data["lux"] < 300:
        actions.append("💡 **조도 확보**: 교실이 어둡습니다. 전체 조명을 점등하세요.")

    if warnings:
        for warn in warnings:
            st.error(warn)
        st.subheader("📢 상황별 즉각 행동 요령")
        for act in actions:
            st.warning(act)
    else:
        st.success("✅ 현재 모니터링 중인 모든 요소가 지정된 안전 기준치 내에 있습니다.")

    st.divider()

    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 실시간 변화 그래프", 
        "📊 통계 분석 (시간대/경향)", 
        "📋 누적 측정 데이터 표", 
        "💡 요소별 용어 & 측정 장비 안내"
    ])

    with tab1:
        st.subheader("시간대별 환경 수치 변화 추이")
        if len(st.session_state.history) > 0:
            latest_time = st.session_state.history.iloc[-1]["시간"]
            st.markdown(f"⏱️ **최신 데이터 업데이트 시각**: `{latest_time}`")
            
            col_g1, col_g2 = st.columns(2)
            with col_g1:
                st.markdown("**[현재 단계] 온도(℃) 및 습도(%) 그래프**")
                chart_data1 = st.session_state.history.set_index("시간")[["온도(℃)", "습도(%)"]]
                st.line_chart(chart_data1)
                
            with col_g2:
                st.markdown("**[현재 단계] 초미세먼지(µg/m³) 및 CO₂(ppm) 그래프**")
                chart_data2 = st.session_state.history.set_index("시간")[["초미세먼지(µg/m³)", "CO2(ppm)"]]
                st.line_chart(chart_data2)

            if len(st.session_state.history) > 1:
                st.markdown("---")
                st.markdown("""
                <div>
                    <span class="badge-previous">📋 이전 측정 단계 데이터 기록</span>
                    <span style="color: #6c757d; font-size: 0.9rem; margin-left: 8px;">
                        (직전 주기 데이터와 비교할 수 있도록 전 단계 그래프가 함께 표시됩니다)
                    </span>
                </div>
                """, unsafe_allow_html=True)
                
                prev_history = st.session_state.history.iloc[:-1]
                prev_time = prev_history.iloc[-1]["시간"]
                
                st.caption(f"⌛ 이전 단계 측정 시각: `{prev_time}`")
                col_pg1, col_pg2 = st.columns(2)
                with col_pg1:
                    st.markdown("*[이전 단계] 온도 & 습도*")
                    p_chart1 = prev_history.set_index("시간")[["온도(℃)", "습도(%)"]]
                    st.line_chart(p_chart1)
                with col_pg2:
                    st.markdown("*[이전 단계] 초미세먼지 & CO₂*")
                    p_chart2 = prev_history.set_index("시간")[["초미세먼지(µg/m³)", "CO2(ppm)"]]
                    st.line_chart(p_chart2)

    with tab2:
        st.subheader("📊 교실 환경 데이터 통계 및 요약 분석")
        
        if len(st.session_state.history) > 0:
            df_stats = st.session_state.history.copy()
            
            col_st1, col_st2, col_st3, col_st4 = st.columns(4)
            with col_st1:
                st.metric("평균 실내 온도", f"{round(df_stats['온도(℃)'].mean(), 1)} ℃")
                st.caption(f"최고: {df_stats['온도(℃)'].max()}℃ / 최저: {df_stats['온도(℃)'].min()}℃")
            with col_st2:
                st.metric("평균 습도", f"{round(df_stats['습도(%)'].mean(), 1)} %")
                st.caption(f"최고: {df_stats['습도(%)'].max()}% / 최저: {df_stats['습도(%)'].min()}%")
            with col_st3:
                st.metric("평균 CO₂ 농도", f"{int(df_stats['CO2(ppm)'].mean())} ppm")
                st.caption(f"최고: {df_stats['CO2(ppm)'].max()}ppm / 최저: {df_stats['CO2(ppm)'].min()}ppm")
            with col_st4:
                st.metric("평균 초미세먼지", f"{round(df_stats['초미세먼지(µg/m³)'].mean(), 1)} µg/m³")
                st.caption(f"최고: {df_stats['초미세먼지(µg/m³)'].max()}µg/m³")

            st.markdown("---")
            st.markdown("#### 🔍 항목별 데이터 수치 분포")
            st.bar_chart(df_stats.set_index("시간")[["CO2(ppm)", "조도(Lux)"]])
        else:
            st.info("누적된 측정 데이터가 없습니다. 모니터링이 시작되면 통계가 표시됩니다.")

    with tab3:
        st.subheader("최근 측정 기록 (최대 20건)")
        col_t1, col_t2, col_t3 = st.columns([3, 1, 1])
        with col_t1:
            st.caption("누적된 측정 데이터를 CSV 파일로 내보내거나 기록을 초기화합니다.")
        with col_t2:
            csv_data = st.session_state.history.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 CSV 다운로드",
                data=csv_data,
                file_name=f"classroom_env_data_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                type="primary"
            )
        with col_t3:
            if st.button("🗑️ 기록 초기화"):
                st.session_state.history = pd.DataFrame(columns=[
                    "시간", "온도(℃)", "습도(%)", "초미세먼지(µg/m³)", "CO2(ppm)", "조도(Lux)", "청정도 등급"
                ])

        st.dataframe(st.session_state.history, use_container_width=True)

        st.markdown("---")
        st.subheader("📄 교실 환경 상태 종합 보고서 요약문 및 정식 다운로드")
        
        col_r1, col_r2 = st.columns([1, 1])
        with col_r1:
            if st.button("📋 요약 보고서 화면 출력하기"):
                avg_temp = round(st.session_state.history["온도(℃)"].mean(), 1)
                avg_co2 = int(st.session_state.history["CO2(ppm)"].mean())
                avg_pm25 = round(st.session_state.history["초미세먼지(µg/m³)"].mean(), 1)
                
                report_text = f"""
                ### 🏫 교실 실내 환경 모니터링 종합 보고서
                - **측정 시각**: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                - **현재 학습 쾌적도 지수**: **{score}점** ({status_text})
                
                #### 1. 주요 측정 항목 평균값 (최근 데이터 기준)
                - **평균 실내 온도**: {avg_temp} ℃ (적정: 18~22℃)
                - **평균 CO₂ 농도**: {avg_co2} ppm (권장: 1,000ppm 이하)
                - **평균 초미세먼지**: {avg_pm25} µg/m³ (권장: 35µg/m³ 이하)
                
                #### 2. 종합 조치 평가
                {'• 모든 항목이 안전 범위 내에 있어 학습에 최적화된 상태입니다.' if score >= 85 else '• 환기 또는 온도 조절이 필요합니다. 상단 행동 요령 가이드를 참고해 주세요.'}
                """
                st.info(report_text)

        with col_r2:
            html_report = generate_html_report(st.session_state.history, score, status_text)
            st.download_button(
                label="📄 정식 보고서 (HTML 파일) 다운로드",
                data=html_report,
                file_name=f"classroom_env_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
                mime="text/html",
                type="primary"
            )

    with tab4:
        st.subheader("📖 교실 모니터링 요약 및 측정 방법 안내")
        st.markdown("""
        | 요소 | 역할 및 목적 | 수치 확인 위치 및 방법 |
        | :--- | :--- | :--- |
        | **🌡️ 온도 (℃)** | 쾌적한 학습 환경 및 실내 온도 관리 | 교실 벽면 온습도계 또는 디지털 온습도 기기 |
        | **💧 습도 (%)** | 정전기 방지 및 바이러스 활성화 억제 | 교실 벽면 온습도계 또는 공기청정기 디스플레이 |
        | **🌫️ 초미세먼지 (µg/m³)** | 호흡기 건강 및 실내 공기질 기준 | 교실용 공기청정기 센서 표시창 또는 휴대용 미세먼지 측정기 |
        | **🫧 CO₂ 농도 (ppm)** | 환기 시점 파악 (졸음 및 집중력 저하 예방) | 실내 대기질 복합 측정기(CO2 전용 측정기) |
        | **💡 조도 (Lux)** | 시력 보호 및 학습 집중도 유지 | 휴대용 조도계(Lux Meter) 또는 스마트폰 조도 측정 앱 |
        | **🏷️ 청정도 등급** | 미세입자 수에 따른 공기 청정도 판단 | 초미세먼지 수치를 기반으로 자동 산출 |
        """)

render_dashboard_fragment()