"""
helpers.py — 공통 유틸리티 함수
"""

from datetime import datetime, timedelta, timezone
from src.utils.constants import (
    KST, CALENDAR_CATEGORY_MAP, MERCHANT_CATEGORY_MAP
)


def utc_str_to_kst(utc_str: str) -> datetime:
    """UTC 문자열 → KST datetime (tzinfo 제거된 naive datetime 반환)"""
    dt = datetime.fromisoformat(utc_str.replace("Z", "+00:00"))
    return dt.astimezone(timezone.utc).replace(tzinfo=None) + KST


def ms_to_kst(ms: int) -> datetime:
    """Unix 밀리초 타임스탬프 → KST datetime"""
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).replace(tzinfo=None) + KST


def assign_sleep_date(bedtime_kst: datetime) -> str:
    """
    취침 시각 기준으로 날짜 할당.
    - 18시 이후 취침 → 당일 날짜
    - 18시 이전(새벽) 취침 → 전날 날짜
    """
    if bedtime_kst.hour >= 18:
        return bedtime_kst.strftime("%Y-%m-%d")
    else:
        return (bedtime_kst - timedelta(days=1)).strftime("%Y-%m-%d")


def classify_calendar_event(summary: str) -> str:
    """이벤트 제목 키워드 → 카테고리"""
    for category, keywords in CALENDAR_CATEGORY_MAP.items():
        if any(kw in summary for kw in keywords):
            return category
    return "기타"


def classify_merchant(merchant: str) -> str:
    """거래처명 키워드 → 소비 카테고리"""
    for category, keywords in MERCHANT_CATEGORY_MAP.items():
        if any(kw in merchant for kw in keywords):
            return category
    return "기타"


def get_weekday_kr(date_str: str) -> str:
    """날짜 문자열 → 한글 요일"""
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return ["월", "화", "수", "목", "금", "토", "일"][dt.weekday()]