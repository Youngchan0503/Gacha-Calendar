def prompt_template(name, title, full_text):
    if name == "업데이트":
        return (
            f"""
            너는 '승리의 여신: 니케'의 공지사항에서 [픽업] 및 [신규 이벤트 스토리] 일정을 추출하는 전문가야.
            아래 규칙에 따라 데이터를 정제하여 JSON 리스트 형식으로 출력해줘.

            [공지 제목]: {title}
            [공지 본문]: {full_text[:8000]}

            ### 추출 및 통합 규칙:
            1. **대상**: 오직 '캐릭터 모집(픽업)'과 '신규 스토리 이벤트'만 추출해. (챌린지 스테이지, 미니게임, 출석 이벤트, 시스템 개선은 모두 무시)
            2. **이벤트 통합**: 
            - 스토리 이벤트가 Part 1, Part 2로 나뉘어 있어도 **하나의 객체**로 합쳐.
            - **title**: 이벤트의 메인 명칭만 사용 (예: "스토리 이벤트 [ARK GUARDIAN]")
            - **start_date**: 전체 이벤트가 시작되는 날짜 (보통 Part 1 시작일)
            - **end_date**: 전체 이벤트가 종료되는 날짜 (모든 파트의 공통 종료일)
            3. **Part 2 처리 (중요)**:
            - 본문에 'Part 2' 혹은 'STORY II'의 시작일이 별도로 명시되어 있다면, **memo** 필드에 "※ Part 2 시작: YYYY-MM-DD HH:MM" 형태로 반드시 기록해.
            - 파트 구분이 없는 단일 스토리 이벤트라면 이 문구는 생략해.
            4. **픽업 처리**:
            - 캐릭터 모집 기간을 추출하여 별도 객체로 생성해.

            ### 출력 JSON 구조 (예시):
            [
            {{
                "game_name": "승리의 여신: 니케",
                "category": "이벤트",
                "title": "스토리 이벤트 [ARK GUARDIAN]",
                "start_date": "2025-12-30 점검 후",
                "end_date": "2026-01-20 04:59",
                "memo": "- 스노우 화이트 과거 회상 스토리\\n- ※ Part 2 시작: 2026-01-06 05:00"
            }},
            {{
                "game_name": "승리의 여신: 니케",
                "category": "픽업",
                "title": "신규 캐릭터 [이름] 모집",
                "start_date": "2025-12-30 점검 후",
                "end_date": "2026-01-20 04:59",
                "memo": "- 속성: 전격\\n- 클래스: 화력형"
            }}
            ]
            """
    )

CONFIG = {
    "game_name": "니케: 승리의 여신",
    "boards": [
        {
            "name": "업데이트", 
            "type": "text",
            "url": "https://game.naver.com/lounge/nikke/board/48",
            "specific_keywords": ["점검&업데이트"],
            "specific_prompt": prompt_template
        }
    ],
    # 이하 공통 설정들...
    "keywords": [], 
    "selectors": {
        # 1. 목록 컨테이너: 가장 표준적인 tbody를 사용 (기존 tr 순회 방식 대응)
        "list_container": "tbody", 
        
        # 2. 게시글 항목: 고정글(fix) 클래스가 없는 tr 안의 a 태그
        # 기존 코드의 if "post_board_fix__jw2yg" in class_name 로직을 CSS로 구현
        "list_items": "tr:not(.post_board_fix__jw2yg) a",
        
        # 3. 본문 영역: 기존 코드에서 확인된 본문 클래스만 타겟팅
        "content": ".detail_wrap_content__1vyDK, .contents-box, .thread-view-content"
    }
}


