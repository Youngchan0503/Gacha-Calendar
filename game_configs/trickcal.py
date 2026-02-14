def prompt_template(name, title, full_text):
    if name == "업데이트":
        return (
            f"""
            너는 게임 공지에서 메인 스토리 업데이트 정보를 추출하여 SQLite DB 구조에 맞게 JSON을 생성하는 전문가야.

            [공지 제목]: {title}
            [공지 본문]: {full_text[:5000]}

            ### 날짜 표준화 규칙:
            1. **형식**: 모든 날짜는 반드시 `YYYY-MM-DD HH:MM` 형식으로 변환해. (예: 2026-02-05 16:00)
            2. **연도**: 본문에 연도가 없다면 현재 연도(2026년)를 적용해.
            3. **시간**: '점검 후' 또는 '정기점검 완료 후'라고 되어 있다면 시간을 `16:00`으로 설정해.
            4. **상시**: '상시' 업데이트인 경우 end_date는 strat_date의 일주일 뒤로 설정해.

            규칙:
            1. 반드시 아래 JSON 키만 사용하여 하나의 객체로 출력해. (마크다운 코드블록 금지)
            2. game_name: 반드시 "트릭컬 리바이브"
            3. title: 공지 제목을 바탕으로 핵심 내용 요약 (예: "메인 스토리 시즌3 2챕터 추가")
            4. category: 반드시 "업데이트"
            5. start_date: 위 규칙을 적용한 표준 날짜 형식      
            6. end_date: 위 규칙을 적용한 표준 날짜 형식
            7. memo: 업데이트되는 에피소드 범위나 주요 특징을 마크다운 형식으로 요약 (예: "- 에피소드: 7~12화 추가\n- 지역: 요정 왕국")

            출력 예시:
            {{"game_name":"트릭컬 리바이브","title":"메인 스토리 시즌3 2챕터 추가","category":"업데이트","start_date":"2026-02-05 16:00","end_date":"2026-02-12 16:00","memo":"- 에피소드: 7~12화 추가"}}
            """
        )
    elif name == "이벤트":
        return (
            f"""
            너는 게임 공지에서 이벤트 및 픽업 정보를 추출하여 SQLite DB 구조에 맞게 JSON을 생성하는 전문가야.

            ### [반드시 준수해야 할 추출 제한]
            - **추출 대상**: 오직 테마극장 정보만 추출할 것.
            - **제외 대상**: 테마극장에 해당하지 않는 '이세계픽셀' 등 다른 모든 내용은 **반드시 무시**해.

            [공지 제목]: {title}
            [공지 본문]: {full_text[:5000]}
            ### 날짜 표준화 규칙:
            1. **형식**: 모든 날짜는 반드시 `YYYY-MM-DD HH:MM` 형식으로 변환해. (예: 2026-02-05 16:00)
            2. **연도**: 본문에 연도가 없다면 현재 연도(2026년)를 적용해.
            3. start_date의 시간이 명시되지 않은 경우 기본값으로 10:59을 사용해.
            4. end_date의 시간이 명시되지 않은 경우 기본값으로 '00:00'을 사용해.
            5. end_date가 명시되지 않은 경우, start_date로부터 7일 후로 설정해.

            ### 출력 및 형식 규칙:
            1. 반드시 마크다운 코드 블록 없이 순수 JSON 리스트 [ {...} ] 형식으로만 출력해.
            2. game_name은 반드시 "트릭컬 리바이브"으로 작성해.
            3. title 작성 규칙: 다야(퓨어샤인) 픽업 (공지 내용에 맞게 구체적으로 작성)
            4. category는 반드시 "이벤트"으로 작성해.
            5. start_date: 위 날짜 규칙을 적용한 표준 날짜 형식
            6. end_date: 위 날짜 규칙을 적용한 표준 날짜 형식
            7. 메모(memo)는 공지의 주요 내용을 간결하게 요약해, 여러 문장일 경우 줄바꿈 문자(\\n)를 사용하여 하나의 문자열로 합쳐서 작성해.

            ### 출력 예시 (반드시 이 형식을 따를 것):
            [
            {{
                "game_name": "트릭컬 리바이브",
                "title": "다야(퓨어샤인) 픽업",
                "category": "이벤트",
                "start_date": "2026-02-13 10:59",
                "end_date": "2026-02-20 00:00",
                "memo": "- 상세 내용\n- 상세 내용\n- 상세 내용"
            }}
            ]
            """
    )

CONFIG = {
    "game_name": "트릭컬 리바이브",
    "boards": [
        {
            "name": "업데이트", 
            "type": "text",
            "url": "https://game.naver.com/lounge/Trickcal/board/11?order=new",
            "specific_keywords": ["업데이트"],
            "must_include": ["메인 스토리가 추가됩니다"],
            "specific_prompt": prompt_template
        },
        {
            "name": "이벤트", 
            "type": "text",
            "url": "https://game.naver.com/lounge/Trickcal/board/13?order=new",
            "specific_keywords": ["신규 픽업", "테마극장"],
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