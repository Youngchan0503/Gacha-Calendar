import sqlite3

def init_db(db_path="game_schedule.db"):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS game_schedules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        game_name TEXT NOT NULL,
        title TEXT NOT NULL,
        category TEXT,
        -- 형식에 구애받지 않도록 TEXT로 설정합니다.
        start_date TEXT,      -- "2025년 1월 25일 정기점검 이후" 등
        end_date TEXT,        -- "상시 판매" 또는 "2026-02-10" 등
        source_url TEXT,
        memo TEXT,
        created_at DATETIME DEFAULT (STRFTIME('%Y-%m-%d %H:%M:%S', 'now', 'localtime'))
    );
    """)

    conn.commit()
    conn.close()
    print(f"DB 생성 완료: {db_path}")

if __name__ == "__main__":
    init_db()