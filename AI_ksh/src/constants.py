"""
constants.py
앱 카테고리 매핑, 코인 정책, 이상치 기준값 등 상수 모음
"""

from datetime import timezone, timedelta

KST = timezone(timedelta(hours=9))

# ── 퀘스트 난이도별 코인 ─────────────────────
COIN_REWARD: dict[str, int] = {
    "easy":   10,
    "normal": 25,
    "hard":   50,
    "hidden":  5,   # 히든 퀘스트 (날씨/상황 조건부)
}

# ── 이상치 판정 기준 (rule-based) ────────────
ANOMALY_THRESHOLDS = {
    "sleep": {
        "min_hours":         7.0,   # 이 미만 → 수면 부족 (퀘스트/리포트)
        "max_hours":         9.0,   # 이 초과 → 과수면 (줄이기 권장)
        "anomaly_min_hours": 4.0,   # 이 미만 → 이상치 (critical)
        "late_bedtime_hour": 2,     # KST 기준 오전 2시 이후 취침 → 늦은 취침
    },
    "steps": {
        "low_threshold":   1000,    # 이 미만 → 극히 적은 활동
        "high_threshold": 20000,    # 이 초과 → 매우 높은 활동 (긍정적)
    },
    "screentime": {
        "max_total_min":     360,   # 6시간 초과 → 과사용
        "max_entertainment": 120,   # 오락성 앱 (게임/유튜브 등) 2시간 초과 → 경고
    },
    "spending": {
        "overspend_threshold": 60000,  # 6만원 초과 → 과소비
    },
}

# ── 기온별 날씨 설명 ─────────────────────────
def get_temp_description(feel_temp_c: float) -> str:
    if feel_temp_c <= 0:    return "많이 추워요 (두꺼운 패딩 필수)"
    elif feel_temp_c <= 5:  return "꽤 추워요 (코트, 패딩 필요)"
    elif feel_temp_c <= 10: return "쌀쌀해요 (자켓, 가디건 필요)"
    elif feel_temp_c <= 17: return "선선해요 (얇은 겉옷 권장)"
    elif feel_temp_c <= 23: return "적당해요 (가벼운 옷차림)"
    elif feel_temp_c <= 28: return "따뜻해요 (반팔 가능)"
    else:                   return "더워요 (시원한 옷차림)"


# ── 이상치 심각도 → 난이도 매핑 ─────────────
# 이상치가 감지된 날은 회복 퀘스트가 Hard로 배정됨
ANOMALY_SEVERITY_TO_DIFFICULTY = {
    "critical": "hard",    # 수면 4h 미만, 스크린타임 8h 초과 등
    "warning":  "normal",  # 수면 5h 미만, 걸음 1000 미만 등
    "mild":     "easy",    # 경미한 이탈
}
