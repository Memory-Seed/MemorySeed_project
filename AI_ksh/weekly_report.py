"""
features/weekly_report.py
주간 리포트 생성 기능

흐름:
  1. 시작~종료 날짜 지정
  2. preprocessor → 주간 요약
  3. anomaly_detector → 날짜별 이상치 탐지
  4. prompt_builder → LLM 프롬프트 조립
  5. LLM API 호출
  6. JSON 파싱 → WeeklyReportResult 반환
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
class WeeklyReportResult:
    period:           dict
    overall_score:    int
    dog_comment:      str
    items:            dict = field(default_factory=dict)
    best_day:         Optional[str] = None
    anomaly_summary:  Optional[str] = None
    next_week_advice: str = ""

    def to_api_format(self) -> dict:
        """Flutter API 형식으로 변환"""
        return {
            "period":         self.period,
            "overallScore":   self.overall_score,
            "dogComment":     self.dog_comment,
            "items": {
                key: {
                    "score":    item.get("score"),
                    "data":     item.get("data"),
                    "feedback": item.get("feedback"),
                }
                for key, item in self.items.items()
            },
            "bestDay":        self.best_day,
            "anomalySummary": self.anomaly_summary,
            "nextWeekAdvice": self.next_week_advice,
        }

    def summary(self) -> str:
        names = {"sleep": "수면", "steps": "걸음수", "screentime": "스크린타임", "spending": "지출", "schedule": "일정"}
        lines = [
            f"[{self.period['start']} ~ {self.period['end']} 주간 리포트]",
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
        if self.best_day:
            lines.append(f"베스트 데이: {self.best_day}")
        if self.anomaly_summary:
            lines.append(f"이번 주: {self.anomaly_summary}")
        lines.append(f"다음 주: {self.next_week_advice}")
        return "\n".join(lines)


# ── 메인 기능 클래스 ─────────────────────────

class WeeklyReportGenerator:
    def __init__(self, preprocessor: LifeDataPreprocessor, llm_caller):
        self.pp     = preprocessor
        self.caller = llm_caller

    def generate(self, start: str | date, end: str | date) -> WeeklyReportResult:
        if isinstance(start, str): start = date.fromisoformat(start)
        if isinstance(end,   str): end   = date.fromisoformat(end)

        # 1. 주간 전처리
        weekly = self.pp.weekly_summary(start, end)

        # 2. 날짜별 이상치 탐지
        history  = self._get_history(start, days=14)
        detector = AnomalyDetector(history=history)
        anomaly_reports = [detector.detect(d) for d in weekly["daily_list"]]

        # 3. 프롬프트 조립
        prompt = PromptBuilder.weekly_report(weekly, anomaly_reports)

        # 4. LLM 호출
        raw = self.caller.call(prompt["system"], prompt["user"])

        # 5. 파싱
        return self._parse({"start": str(start), "end": str(end)}, raw)

    def _parse(self, period: dict, raw: str) -> WeeklyReportResult:
        data = _parse_json(raw)
        return WeeklyReportResult(
            period=period,
            overall_score=data.get("overall_score", 0),
            dog_comment=data.get("dog_comment", ""),
            items=data.get("items", {}),
            best_day=data.get("best_day"),
            anomaly_summary=data.get("anomaly_summary"),
            next_week_advice=data.get("next_week_advice", ""),
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

    DATA_DIR   = os.path.join(os.path.dirname(__file__), "data")
    USE_MOCK   = False      # True: 테스트 / False: 실제 Ollama
    WEEK_START = date(2025, 12, 8)    # ← 시작일 바꾸세요
    WEEK_END   = date(2025, 12, 14)   # ← 종료일 바꾸세요

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

    # JSON 저장
    out_dir  = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"weekly_report_{WEEK_START}_{WEEK_END}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result.to_api_format(), f, ensure_ascii=False, indent=2)
