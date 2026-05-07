"""
models.py
FastAPI Request Body 모델 정의
"""

from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, Field


# ── lifelog_data 내부 구조 ────────────────────

class Transaction(BaseModel):
    id: int
    runId: int
    timestamp: datetime
    amountKrw: int
    merchant: str


class ScreenTimeRecord(BaseModel):
    id: int
    runId: int
    appPackage: str
    startTime: datetime
    endTime: datetime
    durationSec: int


class SleepRecord(BaseModel):
    id: int
    runId: int
    startTime: datetime
    endTime: datetime
    durationMin: int


class StepRecord(BaseModel):
    id: int
    runId: int
    time: datetime
    stepCount: int


class WeatherRecord(BaseModel):
    id: int
    runId: int
    time: datetime
    temperatureC: float
    pm10: Optional[int] = None
    condition: str


class LifelogData(BaseModel):
    transactions: List[Transaction] = Field(default_factory=list)
    screenTimes: List[ScreenTimeRecord] = Field(default_factory=list)
    sleeps: List[SleepRecord] = Field(default_factory=list)
    steps: List[StepRecord] = Field(default_factory=list)
    weathers: List[WeatherRecord] = Field(default_factory=list)


# ── 엔드포인트별 Request Body ─────────────────

class AnalyzeRequest(BaseModel):
    """POST /analyze — 일일 퀘스트 생성 요청"""
    diary_text: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="유저가 작성한 일기 내용 (최대 2000자, null 가능)",
    )
    category: str = Field(
        description="퀘스트 카테고리 (SLEEP, STUDY, EXERCISE, HEALTH, DIGITAL_DETOX, ETC)",
    )
    target_date: Optional[date] = Field(
        default=None,
        description="퀘스트 생성 기준 날짜 (미입력 시 오늘)",
    )
    lifelog_data: LifelogData


class WeeklyReportRequest(BaseModel):
    """POST /report/weekly — 주간 리포트 생성 요청"""
    start_date: Optional[date] = Field(
        default=None,
        description="주 시작일 (월요일)",
    )
    end_date: Optional[date] = Field(
        default=None,
        description="주 종료일 (일요일)",
    )
    lifelog_data: LifelogData


class MonthlyReportRequest(BaseModel):
    """POST /report/monthly — 월간 리포트 생성 요청"""
    year_month: Optional[str] = Field(
        default=None,
        description="년월 (YYYY-MM 형식, 미입력 시 이번 달)",
        pattern=r"^\d{4}-(0[1-9]|1[0-2])$",
    )
    lifelog_data: LifelogData