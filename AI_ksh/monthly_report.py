"""
features/monthly_report.py
월간 리포트 생성 기능

흐름:
  1. 연도/월 지정
  2. preprocessor → 월간 요약 (주차별 breakdown 포함)
  3. anomaly_detector → 날짜별 이상치 탐지
  4. prompt_builder → LLM 프롬프트 조립
  5. LLM API 호출
  6. JSON 파싱 → MonthlyReportResult 반환
"""

import json
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional

from src.preprocessor     import LifeDataPreprocessor
from src.anomaly_detector import AnomalyDetector
from src.prompt_builder   import PromptBuilder
from daily_quest import _parse_json


# ── 결과 모델 ────────────────────────────────

@dataclass
class MonthlyReportResult:
    period:            dict
    overall_score:     int
    dog_comment:       str
    items:             dict = field(default_factory=dict)
    best_week:         Optional[str] = None
    trend_summary:     Optional[str] = None
    next_month_advice: str = ""

    def to_api_format(self) -> dict:
        return {
            "period":          self.period,
            "overallScore":    self.overall_score,
            "dogComment":      self.dog_comment,
            "items": {
                key: {
                    "score":    item.get("score"),
                    "data":     item.get("data"),
                    "feedback": item.get("feedback"),
                }
                for key, item in self.items.items()
            },
            "bestWeek":        self.best_week,
            "trendSummary":    self.trend_summary,
            "nextMonthAdvice": self.next_month_advice,
        }

    def summary(self) -> str:
        names = {"sleep": "수면", "steps": "걸음수", "screentime": "스크린타임", "spending": "지출", "schedule": "일정"}
        p = self.period
        lines = [
            f"[{p['year']}년 {p['month']}월 월간 리포트]",
            f"종합 점수: {self.overall_score}점",
            f"멍코치: {self.dog_comment}",
        ]
        for key in ["sleep", "steps", "screentime", "spending", "schedule"]:
            item = self.items.get(key, {})
            if item:
                score = item.get("score", "-")
                data  = item.get("data", "")
                fb    = item.get("feedback", "")
                lines.append(f"  [{names.get(key, key)} / {score}점] {data}")
                if fb:
                    lines.append(f"    → {fb}")
        if self.best_week:
            lines.append(f"베스트 위크: {self.best_week}")
        if self.trend_summary:
            lines.append(f"이번 달: {self.trend_summary}")
        lines.append(f"다음 달: {self.next_month_advice}")
        return "\n".join(lines)


# ── 메인 기능 클래스 ─────────────────────────

class MonthlyReportGenerator:
    def __init__(self, preprocessor: LifeDataPreprocessor, llm_caller):
        self.pp     = preprocessor
        self.caller = llm_caller

    def generate(self, year: int, month: int) -> MonthlyReportResult:
        # 1. 월간 전처리
        monthly = self.pp.monthly_summary(year, month)

        # 2. 날짜별 이상치 탐지
        first_day = date(year, month, 1)
        history   = self._get_history(first_day, days=14)
        detector  = AnomalyDetector(history=history)
        anomaly_reports = [detector.detect(d) for d in monthly["daily_list"]]

        # 3. 프롬프트 조립
        prompt = PromptBuilder.monthly_report(monthly, anomaly_reports)

        # 4. LLM 호출
        raw = self.caller.call(prompt["system"], prompt["user"])

        # 5. 파싱
        return self._parse(monthly["period"], raw)

    def _parse(self, period: dict, raw: str) -> MonthlyReportResult:
        data = _parse_json(raw)
        return MonthlyReportResult(
            period=period,
            overall_score=data.get("overall_score", 0),
            dog_comment=data.get("dog_comment", ""),
            items=data.get("items", {}),
            best_week=data.get("best_week"),
            trend_summary=data.get("trend_summary"),
            next_month_advice=data.get("next_month_advice", ""),
        )

    def _get_history(self, before: date, days: int) -> list[dict]:
        history = []
        for i in range(days, 0, -1):
            history.append(self.pp.daily_summary(before - timedelta(days=i)))
        return history


if __name__ == "__main__":
    import json, os
    from datetime import date
    from src.llm_caller import LLMCaller, MockLLMCaller

    DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
    USE_MOCK = False      # True: 테스트 / False: 실제 Ollama
    YEAR     = 2025
    MONTH    = 12

    def load(f): return json.load(open(os.path.join(DATA_DIR, f)))
    from src.preprocessor import LifeDataPreprocessor
    pp = LifeDataPreprocessor(
        sleep=load("sleep.json"), steps=load("steps.json"),
        screentime=load("screentime.json"), calendar=load("google_calendar.json"),
        notification=load("notification.json"), weather=load("accuweather.json"),
    )
    caller = MockLLMCaller() if USE_MOCK else LLMCaller()
    result = MonthlyReportGenerator(pp, caller).generate(YEAR, MONTH)
    print(result.summary())

    # JSON 저장
    out_dir  = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"monthly_report_{YEAR}_{MONTH:02d}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result.to_api_format(), f, ensure_ascii=False, indent=2)
