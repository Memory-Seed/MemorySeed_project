"""
features/weekly_quest.py
주간 퀘스트 생성 기능

흐름:
  1. 시작~종료 날짜 지정
  2. preprocessor → 주간 요약
  3. anomaly_detector → 각 날짜별 이상치 탐지
  4. prompt_builder → LLM 프롬프트 조립
  5. LLM API 호출
  6. JSON 파싱 → WeeklyQuestResult 반환
"""

import json
from dataclasses import dataclass, field
from datetime import date, timedelta

from src.preprocessor     import LifeDataPreprocessor
from src.anomaly_detector import AnomalyDetector
from src.prompt_builder   import PromptBuilder
from src.constants        import COIN_REWARD
from daily_quest import Quest, CATEGORY_MAP, _parse_json


# ── 결과 모델 ────────────────────────────────

@dataclass
class WeeklyQuestResult:
    period:          dict           # {"start": "...", "end": "..."}
    weekly_greeting: str
    quests:          list[Quest] = field(default_factory=list)

    def summary(self) -> str:
        lines = [
            f"[{self.period['start']} ~ {self.period['end']} 주간 퀘스트]",
            self.weekly_greeting,
        ]
        for q in self.quests:
            lines.append(
                f"  [{q.difficulty.upper()} / {q.coin_reward}코인] {q.title}\n"
                f"    → {q.description}"
            )
        return "\n".join(lines)

    def to_api_format(self) -> dict:
        """전체 결과를 팀원 Flutter API 형식으로 변환"""
        return {
            "period":  self.period,
            "greeting": self.weekly_greeting,
            "quests":  [q.to_api_format() for q in self.quests],
        }


# ── 메인 기능 클래스 ─────────────────────────

class WeeklyQuestGenerator:
    def __init__(self, preprocessor: LifeDataPreprocessor, llm_caller):
        self.pp     = preprocessor
        self.caller = llm_caller

    def generate(self, start: str | date, end: str | date) -> WeeklyQuestResult:
        if isinstance(start, str): start = date.fromisoformat(start)
        if isinstance(end,   str): end   = date.fromisoformat(end)

        # 1. 주간 전처리
        weekly = self.pp.weekly_summary(start, end)

        # 2. 날짜별 이상치 탐지
        history  = self._get_history(start, days=14)
        detector = AnomalyDetector(history=history)
        anomaly_reports = [detector.detect(d) for d in weekly["daily_list"]]

        # 3. 프롬프트 조립
        prompt = PromptBuilder.weekly_quest(weekly, anomaly_reports)

        # 4. LLM 호출
        raw = self.caller.call(prompt["system"], prompt["user"])

        # 5. 파싱
        return self._parse({"start": str(start), "end": str(end)}, raw)

    def _parse(self, period: dict, raw: str) -> WeeklyQuestResult:
        data     = _parse_json(raw)
        greeting = data.get("weekly_greeting", "")
        quests   = [
            Quest(
                id=q.get("id", f"wq{i}"),
                category=q.get("category", ""),
                title=q.get("title", ""),
                description=q.get("description", ""),
                difficulty=q.get("difficulty", "normal"),
                coin_reward=q.get("coin_reward", COIN_REWARD.get(q.get("difficulty", "normal"), 25)),
                target_value=q.get("target_value"),
                target_unit=q.get("target_unit"),
                reason=q.get("reason", ""),
            )
            for i, q in enumerate(data.get("quests", []))
        ]
        return WeeklyQuestResult(period=period, weekly_greeting=greeting, quests=quests)

    def _get_history(self, before: date, days: int) -> list[dict]:
        history = []
        for i in range(days, 0, -1):
            history.append(self.pp.daily_summary(before - timedelta(days=i)))
        return history


if __name__ == "__main__":
    import json, os
    from datetime import date
    from llm_caller import LLMCaller, MockLLMCaller

    DATA_DIR   = os.path.join(os.path.dirname(__file__), "data")
    USE_MOCK   = False      # True: 테스트 / False: 실제 Ollama

    # 전 주 자동 계산 (오늘 기준 지난 월~일)
    today      = date.today()
    # 이번 주 월요일 = 오늘 - 요일수
    this_monday = today - __import__("datetime").timedelta(days=today.weekday())
    WEEK_START  = this_monday - __import__("datetime").timedelta(days=7)  # 저번 주 월요일
    WEEK_END    = this_monday - __import__("datetime").timedelta(days=1)  # 저번 주 일요일
    # 직접 지정하려면 아래 주석 해제
    # WEEK_START = date(2025, 12, 8)
    # WEEK_END   = date(2025, 12, 14)

    def load(f): return json.load(open(os.path.join(DATA_DIR, f)))
    from src.preprocessor import LifeDataPreprocessor
    pp = LifeDataPreprocessor(
        sleep=load("sleep.json"), steps=load("steps.json"),
        screentime=load("screentime.json"), calendar=load("google_calendar.json"),
        notification=load("notification.json"), weather=load("accuweather.json"),
    )
    caller = MockLLMCaller() if USE_MOCK else LLMCaller()
    result = WeeklyQuestGenerator(pp, caller).generate(WEEK_START, WEEK_END)
    print(result.summary())

    # JSON 저장
    out_dir  = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"weekly_quest_{WEEK_START}_{WEEK_END}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result.to_api_format(), f, ensure_ascii=False, indent=2)
    #print(f"\n저장됨 → {out_path}")
