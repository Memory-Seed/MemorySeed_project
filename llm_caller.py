"""
llm_caller.py
LLM 호출 모듈 — Ollama (OpenAI 호환 API) 기반

기본값:
  base_url : http://localhost:11434/v1   (OLLAMA_BASE_URL 환경변수로 변경)
  api_key  : "ollama"                    (OLLAMA_API_KEY 환경변수로 변경)
  model    : qwen2.5:7b                  (OLLAMA_MODEL 환경변수로 변경)

사용법:
  caller = LLMCaller()
  text   = caller.call(system="...", user="...")
"""

import os
import json

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


class LLMCaller:
    def __init__(
        self,
        base_url: str | None = None,
        api_key:  str | None = None,
        model:    str | None = None,
    ):
        if OpenAI is None:
            raise ImportError("openai 패키지가 필요합니다: pip install openai")

        self.client = OpenAI(
            base_url=base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1"),
            api_key=api_key   or os.getenv("OLLAMA_API_KEY",  "ollama"),
        )
        self.model = model or os.getenv("OLLAMA_MODEL", "qwen2.5:7b")

    def call(self, system: str, user: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": user},
            ],
            temperature=0.7,
            max_tokens=1024,
        )
        return response.choices[0].message.content


# ── 테스트용 Mock (Ollama 없이 구조 검증) ────

class MockLLMCaller:
    """Ollama 없이 더미 응답 반환 — 개발/테스트용"""

    MOCK_DAILY_QUEST = {
        "greeting": "오늘도 파이팅이야멍! 어제보다 더 잘할 수 있어멍!",
        "quests": [
            {
                "id": "q1", "category": "운동",
                "title": "오늘 만보 달성멍!",
                "description": "어제 거의 만보 채웠잖아멍! 오늘은 꼭 완성해멍!",
                "target_value": 10000, "target_unit": "보",
                "difficulty": "normal", "coin_reward": 25,
                "is_anomaly_recovery": False,
                "reason": "어제 9,963보라 거의 다 왔어멍!",
            },
            {
                "id": "q2", "category": "수면",
                "title": "자정 전에 자기멍",
                "description": "오늘은 12시 전에 누워보자멍! 내일 더 개운할거야멍!",
                "target_value": None, "target_unit": None,
                "difficulty": "easy", "coin_reward": 10,
                "is_anomaly_recovery": False,
                "reason": "규칙적인 수면이 최고멍!",
            },
            {
                "id": "q3", "category": "스크린타임",
                "title": "음악 앱 2시간 이내멍",
                "description": "음악 들으면서 공부하는 거 좋지만 너무 길면 집중 안되멍!",
                "target_value": 120, "target_unit": "분",
                "difficulty": "hard", "coin_reward": 50,
                "is_anomaly_recovery": False,
                "reason": "어제 Apple Music 131분 사용했어멍!",
            },
        ],
    }

    MOCK_WEEKLY_QUEST = {
        "weekly_greeting": "이번 주 3일이나 이상치가 있었어멍... 같이 회복해보자멍!",
        "quests": [
            {
                "id": "wq1", "category": "수면",
                "title": "이번 주 7h 수면멍",
                "description": "매일 7시간 이상 자는 게 목표야멍! 할 수 있어멍!",
                "target_value": 7, "target_unit": "시간/일",
                "difficulty": "normal", "coin_reward": 25,
                "reason": "평균 수면이 6.9h라 아슬아슬해멍!",
            },
            {
                "id": "wq2", "category": "운동",
                "title": "주간 만보 4일 달성멍",
                "description": "이번 주 만보 달성이 2일뿐이었어멍! 4일 도전해보자멍!",
                "target_value": 4, "target_unit": "일",
                "difficulty": "hard", "coin_reward": 50,
                "reason": "지난주 만보 달성 2일뿐이었어멍!",
            },
            {
                "id": "wq3", "category": "스크린타임",
                "title": "스크린타임 5h 이내멍",
                "description": "하루 5시간 이내로 줄여보자멍! 눈도 쉬어야 해멍!",
                "target_value": 300, "target_unit": "분/일",
                "difficulty": "normal", "coin_reward": 25,
                "reason": "일평균 304분이라 조금만 더 줄여봐멍!",
            },
        ],
    }

    MOCK_DAILY_REPORT = {
        "overall_score": 78,
        "dog_comment": "오늘 거의 만보 걸었어멍! 대단해멍! 근데 수면이 조금 아쉬워멍.",
        "items": {
            "sleep":      {"score": 70, "data": "23:52 취침 → 06:31 기상 (6.7시간)", "feedback": "7시간은 채워야 해멍! 조금 더 자보자멍!"},
            "steps":      {"score": 95, "data": "9,963보", "feedback": "거의 만보야멍! 내일은 꼭 10,000보 채워보자멍!"},
            "screentime": {"score": 80, "data": "총 276분 / 상위: Apple Music 131분, Docs 71분", "feedback": "적당해멍! 음악 들으며 공부했구나멍!"},
            "spending":   {"score": 60, "data": "총 234,400원 (CGV, 11번가)", "feedback": "오늘 좀 많이 썼어멍! 내일은 아껴보자멍!"},
            "schedule":   {"score": 90, "data": "실습/랩, 여자친구 약속", "feedback": "일정 잘 소화했어멍! 행복한 하루였겠다멍!"},
        },
        "anomaly_alert": None,
        "tomorrow_weather": "2.1~8.9°C, 강수확률 19%",
        "tomorrow_comment": "내일 꽤 추워멍! 따뜻하게 입고 나가자멍!",
    }

    MOCK_WEEKLY_REPORT = {
        "overall_score": 65,
        "dog_comment": "이번 주 3일이나 컨디션이 안 좋았어멍... 많이 힘들었지? 멍코치가 걱정했어멍.",
        "items": {
            "sleep":      {"trend": "stable",    "data": "평균 6.9h, 평균 취침 23:25, 기상 08:14", "feedback": "수면은 안정적이야멍! 취침 시간 조금 더 앞당겨보자멍!"},
            "steps":      {"trend": "improving", "data": "주간 총 66,689보, 일평균 9,527보, 만보 달성 2일", "feedback": "걸음수 늘고 있어멍! 만보 달성일 더 늘려보자멍!"},
            "screentime": {"trend": "declining", "data": "일평균 304분, 상위: SoundCloud, PUBG", "feedback": "게임 시간이 좀 많아멍! 조금만 줄여보자멍!"},
            "spending":   {"trend": "stable",    "data": "주간 총 지출 집계", "feedback": "적당하게 잘 쓰고 있어멍!"},
            "schedule":   {"trend": "stable",    "data": "총 19개 일정, 수업 6회, 약속 3회", "feedback": "바쁜 한 주였구나멍! 잘 소화했어멍!"},
        },
        "best_day": "2025-12-10",
        "anomaly_summary": "3일 컨디션 저조했어멍. 특히 수면 시간이 불규칙했어멍.",
        "next_week_advice": "다음 주는 취침 시간 고정이 목표야멍! 같이 해보자멍!",
    }

    def call(self, system: str, user: str) -> str:
        if "일간 퀘스트" in user or "일일 퀘스트" in user:
            return json.dumps(self.MOCK_DAILY_QUEST,  ensure_ascii=False)
        if "주간 퀘스트" in user:
            return json.dumps(self.MOCK_WEEKLY_QUEST, ensure_ascii=False)
        if "오늘 하루 리포트" in user:
            return json.dumps(self.MOCK_DAILY_REPORT, ensure_ascii=False)
        if "주간 리포트" in user:
            return json.dumps(self.MOCK_WEEKLY_REPORT, ensure_ascii=False)
        return json.dumps({"error": "unknown"}, ensure_ascii=False)
