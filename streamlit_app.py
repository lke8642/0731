import streamlit as st
import pandas as pd
import random
from openai import OpenAI

# 🔗 외부 Google Sheet CSV 링크 (게시 후 pub?output=csv 형태로)
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vT_H3-wlNngYonW1CXObdK1FsUc0GRqyN0xWBAB4VXwetAlzm8jV_t0yewofuEJgxqi6SpUhKwtyXKt/pub?gid=0&single=true&output=csv"

# 데이터 불러오기
@st.cache_data
def load_data():
    df = pd.read_csv(CSV_URL)
    df = df.sample(frac=1).reset_index(drop=True)
    return df

df = load_data()

st.set_page_config(page_title="ます형 챌린지", layout="wide")
st.title("📘 ます형 챌린지 - 일본어 동사 마스터")
st.markdown("#### 동사의 정중한 표현을 골라보세요!")

score = 0

client = OpenAI(api_key=st.secrets["openai_api_key"])
# OpenAI 클라이언트 초기화

def generate_multiple_choice(question: str, correct_answer: str):
    # 프롬프트 설정
    prompt = f"""
다음 문제의 정답은 "{correct_answer}"입니다. 이 정답을 포함하여 총 5개의 보기 중 1개로 넣고,
나머지 4개의 보기(오답)는 그럴듯하지만 틀린 보기로 생성하세요.

출력은 보기 4개만 쉼표로 구분해서 반환하세요. 정답은 포함하지 마세요.

문제: {question}
정답: {correct_answer}
"""
    # ChatGPT에 요청
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1        
    )

    # 모델이 생성한 오답 리스트
    wrong_choices_raw = response.choices[0].message.content.strip()
    wrong_choices = [choice.strip() for choice in wrong_choices_raw.split(",")]

    # 4개만 사용하도록 보정
    if len(wrong_choices) > 4:
        wrong_choices = wrong_choices[:4]
    if len(wrong_choices) != 4:
        raise ValueError(f"모델이 잘못된 개수의 보기를 반환했습니다: {wrong_choices}")

    return {
        "question": question,
        "options": wrong_choices
    }

# 컬럼명 확인 및 KeyError 방지
# CSV 파일의 컬럼명이 '정중형'이 아니라 'ます형'일 가능성이 높으므로, 컬럼명을 맞춰줍니다.
# '정중형' → 'ます형' 으로 변경

for i, row in df.iterrows():
    st.subheader(f"Q{i+1}. 「{row['동사 원형']}」의 정중한 표현은?")

    # row["ます형"]을 정답으로 사용
    w_answers = generate_multiple_choice(f"「{row['동사 원형']}」의 정중한 표현은?", row["정중한 표현"])

    options = [row["정중한 표현"], *w_answers['options']]
    random.shuffle(options)

    selected = st.radio("선택하세요:", options, key=i)

    if selected == row["정중한 표현"]:
        st.success("정답입니다!")
        score += 1
    else:
        st.error(f"틀렸습니다. 정답은 {row['정중한 표현']}입니다.")

    st.caption(f"해설: {row['해설']}")
    st.markdown("---")

st.markdown(f"### ✅ 최종 점수: {score} / {len(df)}")
st.slider("이번 학습 자신감은?", 1, 5, 3)
st.button("다시 도전하기")
st.markdown("---")