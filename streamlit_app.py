import streamlit as st
import pandas as pd
import random
import re
import time
from openai import OpenAI
from gtts import gTTS
from io import BytesIO

# ✅ CSV URL
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vT_H3-wlNngYonW1CXObdK1FsUc0GRqyN0xWBAB4VXwetAlzm8jV_t0yewofuEJgxqi6SpUhKwtyXKt/pub?gid=0&single=true&output=csv"

# ✅ Load data
@st.cache_data
def load_data():
    df = pd.read_csv(CSV_URL)
    df = df.sample(frac=1).reset_index(drop=True)
    return df

df_all = load_data()
df = pd.concat([df_all] * ((20 // len(df_all)) + 1), ignore_index=True).head(20)

# ✅ Streamlit setting
st.set_page_config(page_title="ます형 챌린지", layout="wide")
st.title("📘 ます형 챌린지 - 일본어 동사 마스터")
st.markdown("#### 동사의 정중한 표현을 골라보세요! (총 20문제, 문제당 5점)")

# ✅ OpenAI API
if "openai_api_key" not in st.secrets:
    st.error("❌ OpenAI API 키가 없습니다. `.streamlit/secrets.toml` 파일을 확인하세요.")
    st.stop()
client = OpenAI(api_key=st.secrets["openai_api_key"])

# ✅ gTTS (음성 생성)
def speak_japanese(text: str) -> BytesIO:
    tts = gTTS(text, lang='ja')
    mp3_fp = BytesIO()
    tts.write_to_fp(mp3_fp)
    mp3_fp.seek(0)
    return mp3_fp

# ✅ GPT 보기 생성
@st.cache_data(show_spinner=False)
def generate_multiple_choice(question: str, correct_answer: str):
    prompt = f"""
    다음 문제의 정답은 \"{correct_answer}\"입니다. 이 정답을 포함하여 총 5개의 보기 중 하나로 넣고, 나머지 4개의 보기(오답)는 그럴듯하지만 틀린 보기로 생성하세요.
    출력 형식 예시:
    보기1: 오답1
    보기2: 오답2
    보기3: 오답3
    보기4: 오답4
    정답은 포함하지 마세요.
    문제: {question}
    정답: {correct_answer}
    """
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )
    raw = response.choices[0].message.content.strip()
    matches = re.findall(r"보기\d+[:：]?\s*(.+)", raw)
    return [m.strip() for m in matches[:4]]

# ✅ 초기 세션 상태 설정
if "initialized" not in st.session_state:
    st.session_state.initialized = False
    st.session_state.score = 0
    st.session_state.start_time = time.time()
    st.session_state.answered_questions = []

if not st.session_state.initialized:
    st.session_state.options_list = []
    for i, row in df.iterrows():
        correct = row["정중한 표현"]
        q_text = f"「{row['동사 원형']}」의 정중한 표현은?"
        wrong_options = generate_multiple_choice(q_text, correct)
        options = [correct] + wrong_options
        random.shuffle(options)
        st.session_state.options_list.append(options)
    st.session_state.initialized = True

# ✅ 문제 루프
for i, row in df.iterrows():
    st.subheader(f"Q{i+1}. 「{row['동사 원형']}」의 정중한 표현은?")
    options = st.session_state.options_list[i]
    selected = st.radio("選択してください:", ["-- 선택해주세요 --"] + options, key=f"q_{i}", index=0)
    correct = row["정중한 표현"]

    with st.expander("🗣️ 일본어 듣기"):
        if st.button(f"📢 問題再生", key=f"voice_q_{i}"):
            st.audio(speak_japanese(row["동사 원형"]), format="audio/mp3")
        if st.button(f"📢 選択肢再生", key=f"voice_opts_{i}"):
            st.audio(speak_japanese("、".join(options)), format="audio/mp3")

    if selected != "-- 선택해주세요 --" and i not in st.session_state.answered_questions:
        if selected == correct:
            st.success("✅ 정답입니다!")
            st.session_state.score += 5
        else:
            st.error(f"❌ 틀렸습니다. 정답: {correct}")
            st.caption(f"해설: {row['해설']}")
        st.session_state.answered_questions.append(i)
        st.markdown("---")

# ✅ 결과
elapsed = int(time.time() - st.session_state.start_time)
minutes, seconds = divmod(elapsed, 60)
st.markdown(f"### ⏱️ 소요 시간: {minutes}분 {seconds}초")
st.markdown(f"### 🏆 최종 점수: {st.session_state.score} / 100")

# ✅ 칭찬 메시지
if st.session_state.score == 100:
    praise = " 最高ですね！"
elif st.session_state.score >= 95:
    praise = " すごい！"
elif st.session_state.score >= 90:
    praise = " よくできました！"
elif st.session_state.score >= 60:
    praise = " 頑張りましょう!"
else:
    praise = " もう一度!"

st.success(f"{praise}")
st.audio(speak_japanese(praise), format="audio/mp3")

if st.button("🔁 다시 도전하기"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

