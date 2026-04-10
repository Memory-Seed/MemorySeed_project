# src/model/llm_client.py
from __future__ import annotations

import requests
from typing import List

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
MODEL_NAME = "qwen2.5:7b"


def check_ollama_running() -> bool:
    try:
        r = requests.get("http://127.0.0.1:11434/api/tags", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


def get_available_models() -> List[str]:
    try:
        r = requests.get("http://127.0.0.1:11434/api/tags", timeout=5)
        if r.status_code == 200:
            return [m["name"] for m in r.json().get("models", [])]
    except Exception:
        pass
    return []


def ask_llm(prompt: str, model: str = MODEL_NAME, num_ctx: int = 4096) -> str:
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "num_ctx": num_ctx,
            "temperature": 0.2,
        }
    }
    response = requests.post(OLLAMA_URL, json=payload)
    if response.status_code != 200:
        raise RuntimeError(f"Ollama 호출 실패: {response.text}")
    return response.json().get("response", "").strip()


def analyze_daily(summary_text: str, model: str = MODEL_NAME) -> str:
    prompt = f"""
당신은 정량 기반 라이프로그 분석가입니다.

모든 주장에는 숫자를 인용하십시오.
일반적인 조언은 금지합니다.

[출력 형식]
1. 주요 수치 요약
2. 위험 신호
3. 정량 개선 제안 (2개)

[데이터]
{summary_text}
"""
    return ask_llm(prompt, model=model, num_ctx=2048)


# 상관관계 해석 기준 (내부 참조용, 출력에 노출 금지)
_CORR_GUIDE = """
[내부 규칙 — 출력에 절대 노출 금지]
- |r| < 0.30 : 상관 없음. 근거로 사용 금지.
- |r| 0.30~0.49 : 약한 상관. 보조 근거로만 사용. 인과 주장 금지.
- |r| 0.50~0.69 : 중간 상관. 조건부 사용 가능.
- |r| ≥ 0.70 : 강한 상관. 핵심 근거로 사용 가능.
상관값이 없거나 insufficient면 근거로 사용 금지.
corr 값이 weak 이하면 extremes, spending_top_days, top_categories를 근거로 사용.
"""

# 이상치 처리 기준 (내부 참조용, 출력에 노출 금지)
_OUTLIER_GUIDE = """
[이상치 처리 — 출력에 절대 노출 금지]
- spend_krw outlier day가 있으면 해당 날짜 지출을 자연스러운 문장으로 별도 언급.
- spend_mean 대신 spend_median 기준으로 설명.
- "이상치", "IQR", "outlier" 같은 통계 용어는 출력에 쓰지 말 것.
  대신 "특정 날 지출이 크게 몰렸어요" 같은 표현 사용.
"""


def analyze_weekly(weekly_text: str, daily_texts: list, model: str = MODEL_NAME) -> str:
    compressed = "\n".join(
        "\n".join(
            line for line in text.split("\n")
            if any(emoji in line for emoji in ["[", "😴", "🚶", "🌤️", "📅"])
        )
        for text in daily_texts
    )

    prompt = f"""
당신은 사용자의 일상 데이터를 분석해서 친근하고 명확한 언어로 전달하는 라이프 코치입니다.
아래 규칙을 반드시 지키세요.

{_CORR_GUIDE}

{_OUTLIER_GUIDE}

[작성 규칙]
1. 전문 용어 사용 금지
   - 금지: "Driver", "가설", "반증 조건", "corr", "상관 관계", "std", "IQR", "이상치", "outlier"
   - 금지: "~하세요", "~해보세요", "노력해야 해요", "줄여야 해요"
   - 허용: 실제 수치(숫자), 날짜, 요일, 앱 이름, 카테고리명

2. 수치는 반드시 구체적으로 인용할 것
   - 날짜와 요일을 함께 명시 (예: "28일 목요일")
   - 수면: 최대/최솟값 날짜와 시간 모두 인용 (extremes 필드 활용)
   - 스크린: 가장 많이 쓴 앱 이름과 시간 인용 (screen_top_apps 필드 활용)
   - 소비: 가장 지출이 많은 날짜와 금액 인용 (spending_top_days 필드 활용)

3. 카테고리를 연결해서 맥락을 만들 것

4. 문장은 짧고 명확하게. 한 문장에 하나의 메시지만.

5. 말투는 친근하되 가볍지 않게. 반말 금지. "~해요" 체 사용.

6. 지시형 표현 금지
   - 금지: "~하세요", "~해보세요", "노력하세요", "줄이세요"
   - 허용: "~하면 도움이 될 수 있어요", "~을 목표로 해보면 어떨까요"

────────────────────────────────────────
아래 형식을 정확히 따르세요. 섹션을 추가하거나 제거하지 마세요.

한 줄 요약
문장 1개만 작성하세요. 단순 나열 금지.
수면→스크린→소비를 하나의 흐름으로 연결해서 이번 주 이야기처럼 써야 해요.
반드시 포함: 수면 최솟값 날짜+시간, 그날 스크린 최고 앱 이름+시간, 소비 최고 지출일+금액.

📌 이번 주 인사이트
가장 의미 있는 패턴 3개를 작성하세요.
각 인사이트는 2~3문장.
날짜, 수치, 앱 이름, 카테고리명을 반드시 포함.

1.
2.
3.

⚠️ 주의가 필요해요
리스크가 가장 높은 항목 1~2개만. 심각하지 않으면 1개만 써도 됩니다.
날짜와 수치 포함 필수. 지시형 금지. 사실을 전달하는 방식으로.

🎯 다음 주 제안
구체적인 행동 2개. 각각 1~2문장.
반드시 현재 수치 → 목표 수치 형태로 작성.

1.
2.
────────────────────────────────────────

[데이터]
{weekly_text}

[일별 데이터]
{compressed}
"""
    return ask_llm(prompt, model=model, num_ctx=4096)
