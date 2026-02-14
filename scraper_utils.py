import time
import random
import json
import logging
import re
import requests
from google import genai
from google.genai import types
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

    # 설정에서 셀렉터 가져오기
    selectors = config.get('selectors', {})
    list_container_selector = selectors.get('list_container', "tbody")
    list_items_selector = selectors.get('list_items', "tr a")
    content_selector = selectors.get('content', "body")

    try:
        for board in boards:
            logging.info(f"[{config['game_name']} - {board['name']}] 접속 중: {board['url']}")
            driver.get(board['url'])
            time.sleep(random.uniform(3, 5))

            target_keywords = board.get('specific_keywords', config.get('specific_keywords', []))
            
            # 1. 목록 수집 로직: 설정된 컨테이너가 나타날 때까지 대기
            try:
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, list_container_selector)))
                # 설정된 항목 셀렉터(list_items)로 게시글 링크들을 한 번에 수집
                elements = driver.find_elements(By.CSS_SELECTOR, list_items_selector)
            except Exception as e:
                logging.error(f"목록 로딩 실패 (셀렉터: {list_container_selector}): {e}")
                continue

            targets = []
            for el in elements:
                try:
                    title = el.text.strip()
                    href = el.get_attribute("href")

                    # 키워드 매칭 검사
                    if href and any(kw in title for kw in target_keywords):
                        clean_title = title.split('\n')[0]
                        targets.append({"title": clean_title, "url": href})
                except:
                    continue

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
                
                board_type = board.get('type')
                full_text = ""
                image_parts = []
                
                # 2. 본문 및 이미지 추출 로직
                try:
                    # 설정된 content 셀렉터 중 일치하는 요소 대기
                    content_el = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, content_selector)))
                    
                    if board_type == "image":
                        # 본문 영역 내의 모든 이미지 수집
                        imgs = content_el.find_elements(By.TAG_NAME, "img")
                        img_urls = [img.get_attribute("src") for img in imgs if img.get_attribute("src") and "http" in img.get_attribute("src")]
                        
                        # 모든 이미지 다운로드 및 Part 변환 (최대 10개)
                        for img_url in img_urls[:10]:
                            try:
                                img_data = requests.get(img_url, timeout=10).content
                                image_parts.append(types.Part.from_bytes(data=img_data, mime_type="image/jpeg"))
                            except: continue
                        
                        if not image_parts:
                            logging.warning("이미지를 찾을 수 없어 텍스트 분석으로 전환합니다.")
                            full_text = content_el.text
                    else:
                        full_text = content_el.text
                        
                        # 필수 문구 필터링
                        must_include_list = board.get('must_include', [])
                        if must_include_list and not any(text in full_text for text in must_include_list):
                            logging.info(f" ▷ 필수 문구 미포함 스킵")
                            continue
                except Exception as e:
                    logging.error(f"본문 추출 실패: {e}")
                    continue


                
                name = board.get('name')
                prompt_func = board.get('specific_prompt')
                if prompt_func:
                    final_prompt = prompt_func(name, title, full_text)
                else:
                    # 기본 프롬프트가 없을 경우에 대한 예외 처리 로직 필요
                    logging.error("사용 가능한 프롬프트 템플릿이 없습니다.")
                    continue

                try:
                    contents_payload = [final_prompt]
                    if board_type == "image":
                        # 텍스트 명령어 뒤에 이미지 객체들을 추가
                        contents_payload.extend(image_parts)
                        
                        response = client.models.generate_content(
                            model='gemini-2.5-flash', # 이미지 분석 효율이 좋은 2.0 모델 권장
                            contents=contents_payload,
                            config=types.GenerateContentConfig(
                                tools=[types.Tool(google_search=types.GoogleSearch())] 
                            )
                        )
                    else:
                        response = client.models.generate_content(
                            model='gemini-2.5-flash-lite', 
                            contents=final_prompt
                        )

                    response_text = response.text
                    print(response_text)  # AI 응답 원문 출력 (디버깅용)

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