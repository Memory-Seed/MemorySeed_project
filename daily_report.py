"""
features/daily_report.py
일일 리포트 생성 기능

흐름:
  1. 날짜 지정
  2. preprocessor → 일별 요약
  3. anomaly_detector → 이상치 탐지
  4. prompt_builder → LLM 프롬프트 조립
  5. LLM API 호출
  6. JSON 파싱 → DailyReportResult 반환
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
class DailyReportResult:
    date:             str
    overall_score:    int
    dog_comment:      str
    items:            dict = field(default_factory=dict)
    anomaly_alert:    Optional[str] = None
    tomorrow_weather: str = ""
    tomorrow_comment: str = ""

    def to_api_format(self) -> dict:
        """Flutter API 형식으로 변환"""
        return {
            "date":            self.date,
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
            "anomalyAlert":    self.anomaly_alert,
            "tomorrowWeather": self.tomorrow_weather,
            "tomorrowComment": self.tomorrow_comment,
        }

    def summary(self) -> str:
        icons = {"sleep": "수면", "steps": "걸음수", "screentime": "스크린타임", "spending": "지출", "schedule": "일정"}
        lines = [
            f"[{self.date} 일일 리포트]",
            f"종합 점수: {self.overall_score}점",
            f"멍코치: {self.dog_comment}",
        ]
        for key in ["sleep", "steps", "screentime", "spending", "schedule"]:
            item = self.items.get(key, {})
            if item:
                score = item.get("score", "-")
                data  = item.get("data", "")
                fb    = item.get("feedback", "")
                lines.append(f"  [{icons.get(key, key)} / {score}점] {data}")
                if fb:
                    lines.append(f"    → {fb}")
        if self.anomaly_alert:
            lines.append(f"  ⚠️  {self.anomaly_alert}")
        if self.tomorrow_weather:
            lines.append(f"내일 날씨: {self.tomorrow_weather}")
        if self.tomorrow_comment:
            lines.append(f"멍코치: {self.tomorrow_comment}")
        return "\n".join(lines)


# ── 메인 기능 클래스 ─────────────────────────

class DailyReportGenerator:
    def __init__(self, preprocessor: LifeDataPreprocessor, llm_caller):
        self.pp     = preprocessor
        self.caller = llm_caller

    def generate(self, target: str | date, history_days: int = 14) -> DailyReportResult:
        if isinstance(target, str):
            target = date.fromisoformat(target)

        # 1. 전처리
        daily            = self.pp.daily_summary(target)
        tomorrow_summary = self.pp.daily_summary(target + timedelta(days=1))
        history          = self._get_history(target, history_days)

        # 2. 이상치 탐지
        anomaly = AnomalyDetector(history=history).detect(daily)

        # 3. 프롬프트 조립 (내일 날씨 별도로 전달)
        prompt = PromptBuilder.daily_report(
            daily, anomaly,
            tomorrow_weather=tomorrow_summary.get("weather")
        )

        # 4. LLM 호출
        raw = self.caller.call(prompt["system"], prompt["user"])

        # 5. 파싱
        return self._parse(str(target), raw)

    def _parse(self, target_date: str, raw: str) -> DailyReportResult:
        data = _parse_json(raw)
        return DailyReportResult(
            date=target_date,
            overall_score=data.get("overall_score", 0),
            dog_comment=data.get("dog_comment", ""),
            items=data.get("items", {}),
            anomaly_alert=data.get("anomaly_alert"),
            tomorrow_weather=data.get("tomorrow_weather", ""),
            tomorrow_comment=data.get("tomorrow_comment", ""),
        )

    def _get_history(self, before: date, days: int) -> list[dict]:
        history = []
        for i in range(days, 0, -1):
            history.append(self.pp.daily_summary(before - timedelta(days=i)))
        return history


if __name__ == "__main__":
    import json, os
    from datetime import date
    from llm_caller import LLMCaller, MockLLMCaller

    DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
    USE_MOCK = False        # True: 테스트 / False: 실제 Ollama
    TARGET   = date(2025, 12, 10)   # ← 날짜 바꾸세요

    def load(f): return json.load(open(os.path.join(DATA_DIR, f)))
    from src.preprocessor import LifeDataPreprocessor
    pp = LifeDataPreprocessor(
        sleep=load("sleep.json"), steps=load("steps.json"),
        screentime=load("screentime.json"), calendar=load("google_calendar.json"),
        notification=load("notification.json"), weather=load("accuweather.json"),
    )
    caller = MockLLMCaller() if USE_MOCK else LLMCaller()
    result = DailyReportGenerator(pp, caller).generate(TARGET)
    print(result.summary())

    # JSON 저장
    out_dir  = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"daily_report_{TARGET}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result.to_api_format(), f, ensure_ascii=False, indent=2)
