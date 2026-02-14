from google import genai
from scraper_utils import setup_driver, process_game_scraping
from game_configs import GAMES # __init__.py에서 묶어준 리스트
from json_to_db import save_event_to_db, is_url_exists
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 변수 참조
api_key = os.getenv("API_KEY")
# main.py 수정

def main():
    client = genai.Client(api_key)
    driver = setup_driver()

    try:
        for config in GAMES:
            process_game_scraping(driver, config, client, save_event_to_db, is_url_exists)
    finally:
        driver.quit()

if __name__ == "__main__":
    main()