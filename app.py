import streamlit as st
import sqlite3
import pandas as pd
import os

# DB 경로 설정 (scrapers 폴더 내부 실행 고려)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'game_schedule.db')

# 1. DB 연결 함수
def get_data():
    conn = sqlite3.connect(DB_PATH)
    # 초기 로딩 시에는 ID 역순(최신 등록순)으로 가져옴
    df = pd.read_sql_query("SELECT * FROM game_schedules", conn)
    conn.close()
    return df

# 2. 테스트용 데이터 삽입 (기존 코드 유지)
def insert_test_data():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT count(*) FROM game_schedules")
    if cur.fetchone()[0] == 0:
        sample_data = [
            ('젠레스 존 제로', '2.5 버전 업데이트', '업데이트', '2025-12-30 12:00', '2026-02-10 04:59', 'https://example.com', '밤을 비추는 불씨가 되어'),
            ('니케', '신규 캐릭터 픽업', '픽업', '2025-01-25 10:00', '상시 판매', 'https://example.com', '특별 모집 진행 중')
        ]
        cur.executemany("""
            INSERT INTO game_schedules (game_name, title, category, start_date, end_date, source_url, memo)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, sample_data)
        conn.commit()
    conn.close()

# --- UI 메인 설정 ---
st.set_page_config(page_title="게임 일정 대시보드", layout="wide")
insert_test_data()
df = get_data()

# 상단 타이틀 및 필터 영역
st.title("🎮 게임 업데이트 및 픽업 일정")
st.write("SQLite에서 불러온 실시간 데이터입니다.")

# --- 사이드바 필터 및 정렬 기능 ---
st.sidebar.header("🔍 필터 및 정렬")

# 1. 게임별 필터
game_list = ["전체"] + list(df['game_name'].unique())
selected_game = st.sidebar.selectbox("게임 선택", game_list)

# 2. 정렬 기준
sort_option = st.sidebar.radio("정렬 기준", ["최신 등록순", "시작 날짜순", "종료 날짜순"])

# 데이터 필터링 적용
if selected_game != "전체":
    df = df[df['game_name'] == selected_game]

# 데이터 정렬 적용
if sort_option == "최신 등록순":
    df = df.sort_values(by="id", ascending=False)
elif sort_option == "시작 날짜순":
    df = df.sort_values(by="start_date", ascending=True)
elif sort_option == "종료 날짜순":
    # '상시'나 텍스트가 섞여있을 수 있어 정렬 시 주의 필요
    df = df.sort_values(by="end_date", ascending=True)

st.divider()

# 3. 카드 레이아웃으로 데이터 출력
if not df.empty:
    # 한 줄에 3개씩 배치하여 가독성 향상
    cols = st.columns(3)
    
    for idx, (i, row) in enumerate(df.iterrows()):
        with cols[idx % 3]:
            with st.container(border=True):
                st.subheader(f"{row['game_name']}")
                st.info(f"📁 {row['category']} | {row['title']}")
                
                st.write(f"📅 **시작:** {row['start_date']}")
                st.write(f"⌛ **종료:** {row['end_date']}")
                
                if row['memo']:
                    with st.expander("내용 요약 및 메모"):
                        st.markdown(row['memo'])
                
                if row['source_url']:
                    st.link_button("공지 원문 보기", row['source_url'], use_container_width=True)
else:
    st.info("조건에 맞는 일정이 없습니다.")