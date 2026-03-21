"""
daily_quest.py
일일 퀘스트 생성 기능
"""

import json
import re
from dataclasses import dataclass, field
from datetime import date, timedelta

from src.preprocessor     import LifeDataPreprocessor
from src.anomaly_detector import AnomalyDetector
from src.prompt_builder   import PromptBuilder
from src.constants        import COIN_REWARD


# 내부 카테고리 → 팀원 API 카테고리 매핑
CATEGORY_MAP = {
    "수면":      "SLEEP",
    "운동":      "EXERCISE",
    "스크린타임": "DIGITAL_DETOX",
    "생산성":    "STUDY",
    "건강":      "HEALTH",
    "지출":      "ETC",
    "일정":      "STUDY",
    "날씨":      "WEATHER",
}


@dataclass
class Quest:
    id:                  str
    category:            str
    title:               str
    description:         str
    difficulty:          str
    coin_reward:         int
    is_anomaly_recovery: bool = False
    target_value:        float | None = None
    target_unit:         str   | None = None
    reason:              str   = ""
    is_completed:        bool  = False

    def to_api_format(self) -> dict:
        """팀원 Flutter API 형식으로 변환"""
        return {
            "title":       self.title,
            "description": self.description,
            "category":    CATEGORY_MAP.get(self.category, "ETC"),
            "targetValue": int(self.target_value) if self.target_value else None,
            "difficulty":  self.difficulty.upper(),
            "coinReward":  self.coin_reward,
        }


@dataclass
class DailyQuestResult:
    date:          str
    greeting:      str
    quests:        list[Quest] = field(default_factory=list)
    hidden_quests: list[Quest] = field(default_factory=list)

    def summary(self) -> str:
        lines = [f"[{self.date} 일일 퀘스트]", self.greeting]
        for q in self.quests:
            tag = " 회복" if q.is_anomaly_recovery else ""
            lines.append(
                f"  [{q.difficulty.upper()} / {q.coin_reward}코인]{tag} {q.title}\n"
                f"    -> {q.description}"
            )
        if self.hidden_quests:
            lines.append("  [히든 퀘스트]")
            for q in self.hidden_quests:
                lines.append(
                    f"  [HIDDEN / {q.coin_reward}코인] {q.title}\n"
                    f"    -> {q.description}"
                )
        return "\n".join(lines)

    def to_api_format(self) -> dict:
        """전체 결과를 팀원 Flutter API 형식으로 변환"""
        return {
            "date":    self.date,
            "greeting": self.greeting,
            "quests":  [q.to_api_format() for q in self.quests],
            "hiddenQuests": [q.to_api_format() for q in self.hidden_quests],
        }


class DailyQuestGenerator:
    def __init__(self, preprocessor: LifeDataPreprocessor, llm_caller):
        self.pp     = preprocessor
        self.caller = llm_caller

    def generate(self, target: str | date, history_days: int = 14) -> DailyQuestResult:
        if isinstance(target, str):
            target = date.fromisoformat(target)

        # 일일 퀘스트는 전날 데이터 기준으로 생성
        yesterday = target - timedelta(days=1)
        daily     = self.pp.daily_summary(yesterday)
        history   = self._get_history(yesterday, history_days)
        anomaly   = AnomalyDetector(history=history).detect(daily)

        today_summary = self.pp.daily_summary(target)
        today_cal     = self.pp._calendar(target)               # 오늘 일정
        today_weather = today_summary.get("weather")            # 오늘 날씨 (히든 퀘스트용)
        tomorrow_cal  = self.pp._calendar(target + timedelta(days=1))  # 내일 일정

        prompt = PromptBuilder.daily_quest(
            daily, anomaly,
            tomorrow_calendar=tomorrow_cal,
            today_calendar=today_cal,
            today_weather=today_weather,
        )
        raw     = self.caller.call(prompt["system"], prompt["user"])
        return self._parse(str(target), raw)

    def _parse(self, target_date: str, raw: str) -> DailyQuestResult:
        data     = _parse_json(raw)
        greeting = data.get("greeting", "")

        def parse_quest(q, i, prefix="q"):
            return Quest(
                id=q.get("id", f"{prefix}{i}"),
                category=q.get("category", ""),
                title=q.get("title", ""),
                description=q.get("description", ""),
                difficulty=q.get("difficulty", "normal"),
                coin_reward=q.get("coin_reward", COIN_REWARD.get(q.get("difficulty", "normal"), 25)),
                is_anomaly_recovery=q.get("is_recovery", False),
                target_value=q.get("target_value"),
                target_unit=q.get("target_unit"),
                reason=q.get("reason", ""),
            )

        quests        = [parse_quest(q, i) for i, q in enumerate(data.get("quests", []))]
        hidden_quests = [parse_quest(q, i, "hq") for i, q in enumerate(data.get("hidden_quests", []))]

        return DailyQuestResult(
            date=target_date,
            greeting=greeting,
            quests=quests,
            hidden_quests=hidden_quests,
        )

    def _get_history(self, before: date, days: int) -> list[dict]:
        history = []
        for i in range(days, 0, -1):
            history.append(self.pp.daily_summary(before - timedelta(days=i)))
        return history


def _parse_json(text: str) -> dict:
    text = text.strip()

    if "```" in text:
        parts = text.split("```")
        for part in parts:
            part = part.strip()
            if part.startswith("json"):
                part = part[4:].strip()
            if part.startswith("{"):
                text = part
                break

    start = text.find("{")
    end   = text.rfind("}") + 1
    if start != -1 and end > start:
        text = text[start:end]

    control = "".join(chr(i) for i in list(range(0, 9)) + list(range(11, 13)) + list(range(14, 32)))
    text = text.translate(str.maketrans("", "", control))
    text = text.replace(chr(10), " ").replace(chr(13), " ").replace(chr(9), " ")

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return json.loads(text, strict=False)


if __name__ == "__main__":
    import json, os
    from datetime import date
    from llm_caller import LLMCaller, MockLLMCaller

    DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
    USE_MOCK = False        # True: 테스트 / False: 실제 Ollama
    TARGET   = date(2025, 12, 10)   # <- 날짜 바꾸세요

    def load(f): return json.load(open(os.path.join(DATA_DIR, f)))
    from src.preprocessor import LifeDataPreprocessor
    pp = LifeDataPreprocessor(
        sleep=load("sleep.json"), steps=load("steps.json"),
        screentime=load("screentime.json"), calendar=load("google_calendar.json"),
        notification=load("notification.json"), weather=load("accuweather.json"),
    )
    caller = MockLLMCaller() if USE_MOCK else LLMCaller()
    result = DailyQuestGenerator(pp, caller).generate(TARGET)
    print(result.summary())

    # JSON 저장
    out_dir  = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"daily_quest_{TARGET}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result.to_api_format(), f, ensure_ascii=False, indent=2)
    #print(f"\n저장됨 → {out_path}")
