def prompt_template(name, title, full_text):
    if name == "업데이트":
        return (
            f"""
            너는 '블루 아카이브' 공지에서 [신규 학생 모집(픽업)] 및 [이벤트] 정보를 추출하여 DB용 JSON을 생성하는 전문가야.
            아래 규칙을 **반드시** 지켜서 결과를 출력해줘.

            ### [반드시 준수해야 할 추출 제한]
            - **추출 대상**: 오직 ①캐릭터 픽업, ②이벤트 스토리 정보만 추출할 것.
            - **제외 대상**: 위 3가지에 해당하지 않는 '총력전', '미니 게임', '2배 캠패인' 등 다른 모든 내용은 **반드시 무시**해.
        

            [공지 제목]: {title}
            [공지 본문]: {full_text[:8000]}

            ### 1. 캐릭터 픽업 (Pickup) 규칙:
            - **통합 저장**: 동일 기간에 진행되는 모든 픽업 캐릭터는 하나의 객체로 합쳐.
            - **title**: 캐릭터 이름을 「 」와 &로 연결해. (예: 「미요」&「후유」&「사츠키」)
            - **memo**: 각 캐릭터별로 [신규] 또는 [복각] 여부를 명시하고 특징을 짧게 적어.
                (예: - 미요: [신규] 스트라이커, 관통 / - 사츠키: [복각] 스페셜, 신비)

            ### 2. 이벤트 (Event) 규칙:
            - **title**: 이벤트 명칭만 깔끔하게 추출. (예: 분쟁 지대 #1)
            - **memo**: [신규] 또는 [복각] 여부를 첫 줄에 적고, 관련 TMI나 주요 보상을 리스트로 적어.

            ### 3. 공통 규칙:
            - **날짜**: YYYY-MM-DD HH:MM 형식으로 변환. (점검 후 시작인 경우 공지된 종료 예정 시간을 기준으로 작성)
            - **game_name**: 반드시 "블루 아카이브"로 설정.
            - **출력**: JSON 리스트 형식 [ {{...}}, {{...}} ]으로 출력.

            ### 출력 예시:
            [
                {{
                "game_name": "블루 아카이브",
                "category": "픽업",
                "title": "「미요」&「후유」&「사츠키」",
                "start_date": "2026-02-10 11:00",
                "end_date": "2026-02-24 10:59",
                "memo": "- 미요: [신규] 스트라이커/관통\\n- 후유: [신규] 스페셜/폭발\\n- 사츠키: [복각] 스트라이커/신비"
                }},
                {{
                "game_name": "블루 아카이브",
                "category": "이벤트",
                "title": "누구를 위한 예술인가 ~위작과 미학의 행방~",
                "start_date": "2026-02-10 11:00",
                "end_date": "2026-02-17 03:59",
                "memo": "- 임무 Normal 2-3 클리어 시 "누구를 위한 예술인가 ~위작과 미학의 행방~" 이벤트를 진행할 수 있습니다."
                }}
            ]
            """
        )
    

CONFIG = {
    "game_name": "블루아카이브",
    "boards": [
        {
            "name": "업데이트", 
            "type": "text",
            "url": "https://forum.nexon.com/bluearchive/board_list?board=1076",
            "specific_keywords": ["상세 안내"],
            "specific_prompt": prompt_template
        }
    ],
    # 이하 공통 설정들...
    "keywords": [], 
    "selectors": {
        # 1. 목록 컨테이너: 가장 표준적인 tbody를 사용 (기존 tr 순회 방식 대응)
        "list_container": "tbody, ul.type-list", 
        
        # 2. 게시글 항목: 고정글(fix) 클래스가 없는 tr 안의 a 태그
        # 기존 코드의 if "post_board_fix__jw2yg" in class_name 로직을 CSS로 구현
        "list_items": "tr:not(.post_board_fix__jw2yg) a, ul.type-list li a",
        
        # 3. 본문 영역: 기존 코드에서 확인된 본문 클래스만 타겟팅
        "content": ".detail_wrap_content__1vyDK, .contents-box, .thread-view-content"
    }
}