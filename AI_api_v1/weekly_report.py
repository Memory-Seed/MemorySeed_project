"""
features/weekly_report.py
주간 리포트 생성 기능
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
class WeeklyReportResult:
    period:       dict
    weekly_summary: str
    top_emotion:  str
    growth_tip:   str
    weekly_score: int

    def to_api_format(self) -> dict:
        return {
            "weekly_summary": self.weekly_summary,
            "top_emotion":    self.top_emotion,
            "growth_tip":     self.growth_tip,
            "weekly_score":   self.weekly_score,
        }

    def summary(self) -> str:
        return (
            f"[{self.period['start']} ~ {self.period['end']} 주간 리포트]\n"
            f"종합 점수: {self.weekly_score}점\n"
            f"감정: {self.top_emotion}\n"
            f"요약: {self.weekly_summary}\n"
            f"조언: {self.growth_tip}"
        )


class WeeklyReportGenerator:
    def __init__(self, preprocessor: LifeDataPreprocessor, llm_caller):
        self.pp     = preprocessor
        self.caller = llm_caller

    def generate(self, start: str | date, end: str | date) -> WeeklyReportResult:
        if isinstance(start, str): start = date.fromisoformat(start)
        if isinstance(end,   str): end   = date.fromisoformat(end)

        weekly  = self.pp.weekly_summary(start, end)
        history = self._get_history(start, days=14)
        detector = AnomalyDetector(history=history)
        anomaly_reports = [detector.detect(d) for d in weekly["daily_list"]]

        prompt = PromptBuilder.weekly_report(weekly, anomaly_reports)
        raw    = self.caller.call(prompt["system"], prompt["user"])
        return self._parse({"start": str(start), "end": str(end)}, raw)

    def _parse(self, period: dict, raw: str) -> WeeklyReportResult:
        data = _parse_json(raw)
        return WeeklyReportResult(
            period=period,
            weekly_summary=data.get("weekly_summary", ""),
            top_emotion=data.get("top_emotion", ""),
            growth_tip=data.get("growth_tip", ""),
            weekly_score=int(data.get("weekly_score", 0)),
        )

    def _get_history(self, before: date, days: int) -> list[dict]:
        history = []
        for i in range(days, 0, -1):
            history.append(self.pp.daily_summary(before - timedelta(days=i)))
        return history


if __name__ == "__main__":
    import json, os
    from src.llm_caller import LLMCaller, MockLLMCaller

    DATA_DIR   = os.path.join(os.path.dirname(__file__), "data")
    USE_MOCK   = False
    WEEK_START = date(2025, 12, 8)
    WEEK_END   = date(2025, 12, 14)

    def load(f): return json.load(open(os.path.join(DATA_DIR, f)))
    from src.preprocessor import LifeDataPreprocessor
    pp = LifeDataPreprocessor(
        sleep=load("sleep.json"), steps=load("steps.json"),
        screentime=load("screentime.json"), calendar=load("google_calendar.json"),
        notification=load("notification.json"), weather=load("accuweather.json"),
    )
    caller = MockLLMCaller() if USE_MOCK else LLMCaller()
    result = WeeklyReportGenerator(pp, caller).generate(WEEK_START, WEEK_END)
    print(result.summary())

    out_dir  = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"weekly_report_{WEEK_START}_{WEEK_END}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result.to_api_format(), f, ensure_ascii=False, indent=2)