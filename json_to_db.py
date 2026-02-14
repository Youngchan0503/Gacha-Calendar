import json
import sqlite3
import os

# 현재 json_to_db.py 파일의 위치를 기준으로 DB 경로 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "game_schedule.db")

def is_url_exists(source_url: str, db_path=DB_PATH) -> bool:
    """DB에 해당 URL이 이미 저장되어 있는지 확인합니다."""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    try:
        cur.execute("SELECT 1 FROM game_schedules WHERE source_url = ?", (source_url,))
        exists = cur.fetchone() is not None
    except sqlite3.OperationalError:
        exists = False
    conn.close()
    return exists

def save_event_to_db(parsed_json: dict, board_name: str, title: str, source_url: str, db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # AI가 준 데이터 확인용 로그 추가
    print(f"DEBUG - AI 파싱 데이터: {parsed_json}")

    # AI 응답 데이터 추출
    game_name = parsed_json.get("game_name", "알 수 없는 게임")
    display_title = parsed_json.get("title", title)
    category = parsed_json.get("category")
    memo = parsed_json.get("memo")
    
    # --- 날짜 정보 추출 최적화 ---
    # 1. 루트 레벨에서 먼저 찾고 (신규 프롬프트 방식)
    start_date = parsed_json.get("start_date")
    end_date = parsed_json.get("end_date")
    
    # 2. 만약 없다면 period 객체 내부 탐색 (기존 방식 호환)
    if not start_date or not end_date:
        period = parsed_json.get("period", {})
        start_date = start_date or period.get("startDate")
        end_date = end_date or period.get("endDate")

    try:
        cur.execute("""
            INSERT INTO game_schedules (
                game_name, title, category, start_date, end_date, source_url, memo
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (game_name, display_title, category, start_date, end_date, source_url, memo))
        conn.commit()
        # 커밋 직후 행 개수 확인
        cur.execute("SELECT COUNT(*) FROM game_schedules")
        count = cur.fetchone()[0]
        print(f"    [DB 저장 완료] 현재 총 레코드 수: {count}")
    except Exception as e:
        print(f"    [DB 저장 실패] 에러 발생: {e}")
    finally:
        conn.close()