"""
constants.py — 공통 상수 및 매핑 테이블
"""

from datetime import timedelta

# ── 시간 ──────────────────────────────────────
KST = timedelta(hours=9)

# ── 앱 패키지명 → (앱명, 카테고리) ────────────
APP_MAP = {
    "com.google.android.apps.docs":                ("Google Docs",   "생산성"),
    "com.google.android.apps.docs.editors.sheets": ("Google Sheets", "생산성"),
    "com.google.android.calendar":                 ("Google 캘린더",  "생산성"),
    "com.todoist":                                  ("Todoist",       "생산성"),
    "com.google.android.keep":                     ("Google Keep",   "생산성"),
    "com.microsoft.office.onenote":                ("OneNote",       "생산성"),
    "com.samsung.android.app.notes":               ("Samsung Notes", "생산성"),
    "com.google.android.youtube":                  ("YouTube",       "SNS/미디어"),
    "com.instagram.android":                       ("Instagram",     "SNS/미디어"),
    "com.kakao.talk":                              ("KakaoTalk",     "커뮤니케이션"),
    "com.discord":                                 ("Discord",       "커뮤니케이션"),
    "com.naver.linewebtoon":                       ("네이버 웹툰",    "엔터테인먼트"),
    "com.netflix.mediaclient":                     ("Netflix",       "엔터테인먼트"),
    "com.soundcloud.android":                      ("SoundCloud",    "엔터테인먼트"),
    "com.spotify.music":                           ("Spotify",       "엔터테인먼트"),
    "com.apple.android.music":                     ("Apple Music",   "엔터테인먼트"),
    "com.pubg.krmobile":                           ("PUBG Mobile",   "게임"),
    "com.supercell.clashroyale":                   ("Clash Royale",  "게임"),
    "com.android.chrome":                          ("Chrome",        "브라우저"),
    "com.nhn.android.search":                      ("Naver",         "브라우저"),
}

# ── 캘린더 이벤트 카테고리 키워드 ─────────────
CALENDAR_CATEGORY_MAP = {
    "수업":    ["수업", "강의", "교양", "전공"],
    "실습/랩": ["실습", "랩", "lab"],
    "운동":    ["러닝", "산책", "운동", "헬스", "gym"],
    "약속":    ["약속", "만남", "모임"],
    "과제/공부": ["과제", "공부", "스터디", "시험"],
    "동아리":  ["동아리", "클럽"],
}

# ── 거래처 → 소비 카테고리 ────────────────────
MERCHANT_CATEGORY_MAP = {
    "식비": ["서브웨이", "맥도날드", "스타벅스", "메가커피", "이디야", "편의점",
              "GS25", "CU", "세븐일레븐", "야키토리", "홍콩반점", "롯데리아",
              "버거킹", "파리바게뜨", "뚜레쥬르", "할리스", "투썸", "치킨"],
    "쇼핑": ["쿠팡", "이마트", "홈플러스", "롯데마트", "올리브영", "다이소",
              "무신사", "11번가"],
    "교통": ["카카오T", "택시", "버스", "지하철", "주유"],
    "엔터": ["메가박스", "CGV", "롯데시네마", "넷플릭스", "유튜브"],
    "교육": ["학원", "교재", "도서"],
}

# ── 날씨 텍스트 한글 변환 ─────────────────────
WEATHER_CONDITION_KR = {
    "Clear":         "맑음",
    "Mostly sunny":  "대체로 맑음",
    "Partly cloudy": "약간 흐림",
    "Mostly cloudy": "대체로 흐림",
    "Cloudy":        "흐림",
    "Snow":          "눈",
}