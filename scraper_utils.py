import time
import random
import json
import logging
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [%(levelname)s] %(message)s')

def setup_driver():
    """브라우저 감지를 최소화하고 안정적인 크롤링을 위한 드라이버 설정"""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    # webdriver 속성 제거 (봇 탐지 방지)
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })
    return driver

def process_game_scraping(driver, config, client, save_fn, exists_fn):
    """게시판을 순회하며 글을 수집하고 AI 분석 후 DB에 저장"""
    wait = WebDriverWait(driver, 15)
    boards = config.get('boards', [{"name": "기본", "url": config.get('base_url')}])
    
    try:
        for board in boards:
            logging.info(f"[{config['game_name']} - {board['name']}] 접속 중: {board['url']}")
            driver.get(board['url'])
            time.sleep(random.uniform(3, 5))

            # 키워드 우선순위: 보드별 키워드 -> 공통 키워드
            target_keywords = board.get('specific_keywords', config.get('specific_keywords', []))
            
            # 1. 목록 수집 로직 (tr 요소가 나타날 때까지 대기)
            try:
                wait.until(EC.presence_of_all_elements_located((By.TAG_NAME, "tr")))
                rows = driver.find_elements(By.TAG_NAME, "tr")
            except Exception as e:
                logging.error(f"목록 로딩 실패: {e}")
                continue

            targets = []
            for row in rows:
                try:
                    # 공지사항 등 특정 클래스 제외 (기존 로직 유지)
                    class_name = row.get_attribute("class") or ""
                    if "post_board_fix__jw2yg" in class_name:
                        continue

                    link = row.find_element(By.TAG_NAME, "a")
                    title = link.text.strip()
                    href = link.get_attribute("href")

                    if href and any(kw in title for kw in target_keywords):
                        # 제목 내 줄바꿈 제거 (순수 제목만 추출)
                        clean_title = title.split('\n')[0]
                        targets.append({"title": clean_title, "url": href})
                except:
                    continue

            # 중복 URL 제거 및 개수 제한 (테스트용으로 상위 1개만 실행하도록 유지)
            unique_targets = {t['url']: t for t in targets}.values()
            
            for target in list(unique_targets)[:1]:
                url = target.get('url')
                title = target.get('title')
                
                if exists_fn(url):
                    logging.info(f"스킵 (이미 존재): {title}")
                    continue

                logging.info(f"▶ 분석 시작: {title}")
                driver.get(url)
                time.sleep(random.uniform(3, 5))
                
                # 본문 추출
                try:
                    content_el = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, config['selectors']['content'])))
                    full_text = content_el.text
                except:
                    full_text = driver.find_element(By.TAG_NAME, "body").text

                # 본문 필수 문구 필터링
                must_include_list = board.get('must_include', [])
                if must_include_list and not any(text in full_text for text in must_include_list):
                    logging.info(f" ▷ '{board['name']}' 필수 문구 미포함으로 스킵합니다.")
                    continue
                
                prompt_func = board.get('specific_prompt')
                if prompt_func:
                    final_prompt = prompt_func(title, full_text)
                else:
                    # 기본 프롬프트가 없을 경우에 대한 예외 처리 로직 필요
                    logging.error("사용 가능한 프롬프트 템플릿이 없습니다.")
                    continue


                try:
                    # 2. AI 분석 진행 (Gemini 2.0 모델 사용 권장)
                    response = client.models.generate_content(
                        model='gemini-2.5-flash', 
                        contents=final_prompt
                    )
                    response_text = response.text

                    # 3. JSON 파싱 및 정제
                    try:
                        clean_json = response_text.replace("```json", "").replace("```", "").strip()
                        parsed_data = json.loads(clean_json, strict=False)

                        # 결과물 저장 (리스트 형태 대응)
                        if isinstance(parsed_data, list):
                            for item in parsed_data:
                                save_fn(item, config['game_name'], title, url)
                        else:
                            save_fn(parsed_data, config['game_name'], title, url)
                        
                        logging.info(f"    - DB 저장 완료: {title}")
                        
                    except json.JSONDecodeError as je:
                        logging.error(f"JSON 파싱 에러: {je}\n응답 원문: {response_text[:200]}...")
                    except Exception as se:
                        logging.error(f"DB 저장 과정 중 에러: {se}")

                except Exception as ae:
                    logging.error(f"AI 모델 호출 에러: {ae}")

    except Exception as e:
        logging.error(f"스크래핑 중 에러 발생: {e}")