"""
models.py
FastAPI Request Body 모델 정의
"""

from datetime import date
from typing import Optional
from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    """POST /analyze — 일일 퀘스트 생성 요청"""
    diary_text: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="유저가 작성한 일기 내용 (최대 2000자)",
        examples=["오늘 너무 피곤해서 운동을 전혀 못했다."],
    )
    category: str = Field(
        description="퀘스트 카테고리 (SLEEP, STUDY, EXERCISE, HEALTH, DIGITAL_DETOX, ETC)",
        examples=["EXERCISE"],
    )
    target_date: Optional[date] = Field(
        default=None,
        description="퀘스트 생성 기준 날짜 (미입력 시 오늘). 전날 데이터 기반으로 퀘스트 생성됨.",
        examples=["2025-12-10"],
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "diary_text": "오늘 너무 피곤해서 운동을 전혀 못했다.",
                "category": "EXERCISE",
            }
        }
    }


class WeeklyReportRequest(BaseModel):
    """POST /report/weekly — 주간 리포트 생성 요청"""
    start_date: Optional[date] = Field(
        default=None,
        description="주간 시작일 (미입력 시 지난 주 월요일 자동 계산)",
        examples=["2025-12-08"],
    )
    end_date: Optional[date] = Field(
        default=None,
        description="주간 종료일 (미입력 시 지난 주 일요일 자동 계산)",
        examples=["2025-12-14"],
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "start_date": "2025-12-08",
                "end_date":   "2025-12-14",
            }
        }
    }


class MonthlyReportRequest(BaseModel):
    """POST /report/monthly — 월간 리포트 생성 요청"""
    year_month: Optional[str] = Field(
        default=None,
        description="년월 (YYYY-MM 형식, 미입력 시 이번 달 기준)",
        examples=["2025-12"],
        pattern=r"^\d{4}-(0[1-9]|1[0-2])$",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "year_month": "2025-12",
            }
        }
    }