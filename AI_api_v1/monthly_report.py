"""
features/monthly_report.py
월간 리포트 생성 기능
"""

import json
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional

from src.preprocessor     import LifeDataPreprocessor
from src.anomaly_detector import AnomalyDetector
from src.prompt_builder   import PromptBuilder
from daily_quest import _parse_json


@dataclass
class MonthlyReportResult:
    period:           dict
    monthly_insight:  str
    main_keyword:     str
    monthly_score:    int
    cheering_message: str

    def to_api_format(self) -> dict:
        return {
            "monthly_insight":  self.monthly_insight,
            "main_keyword":     self.main_keyword,
            "monthly_score":    self.monthly_score,
            "cheering_message": self.cheering_message,
        }

    def summary(self) -> str:
        p = self.period
        return (
            f"[{p['year']}년 {p['month']}월 월간 리포트]\n"
            f"종합 점수: {self.monthly_score}점\n"
            f"키워드: {self.main_keyword}\n"
            f"인사이트: {self.monthly_insight}\n"
            f"응원: {self.cheering_message}"
        )


class MonthlyReportGenerator:
    def __init__(self, preprocessor: LifeDataPreprocessor, llm_caller):
        self.pp     = preprocessor
        self.caller = llm_caller

    def generate(self, year: int, month: int) -> MonthlyReportResult:
        monthly   = self.pp.monthly_summary(year, month)
        first_day = date(year, month, 1)
        history   = self._get_history(first_day, days=14)
        detector  = AnomalyDetector(history=history)
        anomaly_reports = [detector.detect(d) for d in monthly["daily_list"]]

        prompt = PromptBuilder.monthly_report(monthly, anomaly_reports)
        raw    = self.caller.call(prompt["system"], prompt["user"])
        return self._parse(monthly["period"], raw)

    def _parse(self, period: dict, raw: str) -> MonthlyReportResult:
        data = _parse_json(raw)
        return MonthlyReportResult(
            period=period,
            monthly_insight=data.get("monthly_insight", ""),
            main_keyword=data.get("main_keyword", ""),
            monthly_score=int(data.get("monthly_score", 0)),
            cheering_message=data.get("cheering_message", ""),
        )

    def _get_history(self, before: date, days: int) -> list[dict]:
        history = []
        for i in range(days, 0, -1):
            history.append(self.pp.daily_summary(before - timedelta(days=i)))
        return history


if __name__ == "__main__":
    import json, os
    from src.llm_caller import LLMCaller, MockLLMCaller

    DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
    USE_MOCK = False
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

    out_dir  = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"monthly_report_{YEAR}_{MONTH:02d}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result.to_api_format(), f, ensure_ascii=False, indent=2)