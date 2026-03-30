# src/model/scorer.py
"""
scorer.py — 주간 건강 점수 계산기

실제 데이터 소스:
  - weekly_summary.json  →  sleep.avg_hours / steps.avg_daily
                             screentime.avg_daily_min / finance.total_spent_week
  - daily_records.json   →  수면 std/range, 오락 카테고리별 분, 지출 집중도

점수 설계:
  수면       30점  (평균 시간 + 불안정성 페널티)
  걸음수     25점  (일평균 목표 달성률)
  스크린타임  25점  (총 사용량 + 오락 카테고리 비중)
  소비       20점  (주간 총액 + 집중도 페널티)
  ──────────────────────────────────────────────
  합계      100점   등급 A(90~) B(75~) C(55~) D(35~) E(~35)
"""

from __future__ import annotations

import json
import statistics
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ── 가중치 ────────────────────────────────────────────────────────────────────
WEIGHTS = {"sleep": 30, "steps": 25, "screentime": 25, "spending": 20}

# ── 등급 컷오프 ────────────────────────────────────────────────────────────────
GRADE_CUTOFFS = [(90, "A"), (75, "B"), (55, "C"), (35, "D"), (0, "E")]

# ── 이상치 기준 (constants.py ANOMALY_THRESHOLDS 동기화) ─────────────────────
THR = {
    "sleep": {
        "ideal_min":  7.0,
        "ideal_max":  9.0,
        "crit_min":   4.0,
        "std_penalty_thr": 1.5,   # std 이상 → 안정성 페널티 시작
    },
    "steps": {
        "ideal":  10000,
        "low":     1000,
        "high":   20000,
    },
    "screentime": {
        "max_total_min": 360,
        "max_ent_min":   120,
        # constants.py APP_MAP 카테고리 기준 오락 카테고리
        "ent_categories": {"SNS/미디어", "엔터테인먼트", "게임"},
    },
    "spending": {
        "ideal_weekly":  210000,   # 3만원/일 × 7일
        "limit_weekly":  420000,   # 6만원/일 × 7일
        "top1_penalty_thr": 0.40,  # 하루 집중도 40% 이상 → 집중도 페널티
    },
}

KO = {"sleep": "수면", "steps": "활동", "screentime": "스크린타임", "spending": "소비"}


# ── 유틸 ──────────────────────────────────────────────────────────────────────
def _clamp(v: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, v))


def _grade(score: float) -> str:
    for cutoff, g in GRADE_CUTOFFS:
        if score >= cutoff:
            return g
    return "E"


def _bar(score: float, width: int = 20) -> str:
    filled = round(score / 100 * width)
    return "[" + "█" * filled + "░" * (width - filled) + "]"


# ── 데이터클래스 ──────────────────────────────────────────────────────────────
@dataclass
class ItemScore:
    category:  str
    raw_score: float
    weighted:  float
    grade:     str
    weight:    int
    detail:    dict
    flags:     List[str]


@dataclass
class WeeklyScore:
    week:         str
    total:        float
    grade:        str
    items:        Dict[str, ItemScore]
    summary_line: str
    score_block:  str = field(default="")


# ── 항목별 점수 계산 ──────────────────────────────────────────────────────────

def _score_sleep(
    ws: dict,
    daily_records: dict,
    dates: List[str],
) -> Tuple[float, List[str], dict]:
    """
    ws["sleep"] = { avg_hours, vs_baseline }   ← weekly_summary.json
    daily_records → duration_hours 로 std/range 직접 계산
    """
    flags: List[str] = []
    t = THR["sleep"]

    avg_raw = ws.get("sleep", {}).get("avg_hours")
    if avg_raw is None:
        return 0.0, ["수면 데이터 없음"], {"avg_hours": None}

    avg = float(avg_raw)

    # ① 평균 수면 시간 기본 점수 (0~85점)
    if t["ideal_min"] <= avg <= t["ideal_max"]:
        base = 85.0
    elif avg < t["crit_min"]:
        base = _clamp(avg / t["crit_min"] * 15)
        flags.append(f"수면 평균 {avg:.1f}h — critical 부족 ({t['crit_min']}h 미만)")
    elif avg < t["ideal_min"]:
        base = 15 + (avg - t["crit_min"]) / (t["ideal_min"] - t["crit_min"]) * 70
        flags.append(f"수면 평균 {avg:.1f}h — 권장 {t['ideal_min']}h 미달")
    else:
        over = avg - t["ideal_max"]
        base = _clamp(85 - over * 15)
        flags.append(f"수면 평균 {avg:.1f}h — 권장 {t['ideal_max']}h 초과")

    # ② 수면 안정성 페널티 (std 기반, 최대 -15점)
    sleep_vals = []
    for d in dates:
        rec = daily_records.get(d, {})
        sl = rec.get("sleep")
        if isinstance(sl, dict) and sl.get("duration_hours") is not None:
            sleep_vals.append(float(sl["duration_hours"]))

    sleep_std   = statistics.stdev(sleep_vals)   if len(sleep_vals) >= 2 else None
    sleep_range = max(sleep_vals) - min(sleep_vals) if len(sleep_vals) >= 2 else None

    stability_penalty = 0.0
    if sleep_std is not None and sleep_std >= t["std_penalty_thr"]:
        stability_penalty = _clamp(
            (sleep_std - t["std_penalty_thr"]) / 1.0 * 10, 0, 15
        )
        flags.append(
            f"수면 불안정 — std={sleep_std:.2f}h (기준 {t['std_penalty_thr']}h 이상)"
        )

    if sleep_range is not None and sleep_range > 5.0:
        flags.append(f"수면 범위 과다 — range={sleep_range:.1f}h (>5h, 고위험)")

    detail = {
        "avg_hours":   avg,
        "sleep_std":   round(sleep_std,   2) if sleep_std   is not None else None,
        "sleep_range": round(sleep_range, 2) if sleep_range is not None else None,
        "vs_baseline": ws.get("sleep", {}).get("vs_baseline"),
    }
    return _clamp(base - stability_penalty), flags, detail


def _score_steps(ws: dict) -> Tuple[float, List[str], dict]:
    """ws["steps"] = { avg_daily, vs_baseline }"""
    flags: List[str] = []
    t = THR["steps"]

    avg_raw = ws.get("steps", {}).get("avg_daily")
    if avg_raw is None:
        return 0.0, ["걸음수 데이터 없음"], {"avg_daily": None}

    avg = float(avg_raw)

    if avg >= t["high"]:
        score = 100.0
        flags.append(f"걸음수 {avg:,.0f}보 — 매우 높은 활동 (긍정)")
    elif avg >= t["ideal"]:
        score = 100.0
    elif avg >= t["low"]:
        score = 15 + (avg - t["low"]) / (t["ideal"] - t["low"]) * 85
    else:
        score = _clamp(avg / t["low"] * 15)
        flags.append(f"걸음수 {avg:,.0f}보 — 극저활동 ({t['low']:,}보 미만)")

    detail = {
        "avg_daily":   int(avg),
        "vs_baseline": ws.get("steps", {}).get("vs_baseline"),
    }
    return _clamp(score), flags, detail


def _score_screentime(
    ws: dict,
    daily_records: dict,
    dates: List[str],
) -> Tuple[float, List[str], dict]:
    """
    ws["screentime"] = { avg_daily_min, vs_baseline }
    daily_records["screentime"]["by_category"] → 오락 카테고리 분 계산
    constants.py APP_MAP 카테고리: SNS/미디어, 엔터테인먼트, 게임
    """
    flags: List[str] = []
    t = THR["screentime"]

    avg_raw = ws.get("screentime", {}).get("avg_daily_min")
    if avg_raw is None:
        return 0.0, ["스크린타임 데이터 없음"], {"avg_daily_min": None}

    avg_min = float(avg_raw)

    # ① 총 사용 시간 점수 (0~70점)
    if avg_min <= t["max_total_min"]:
        total_score = 70.0
    else:
        over_h = (avg_min - t["max_total_min"]) / 60
        total_score = _clamp(70 - over_h * 20)
        flags.append(f"스크린타임 {avg_min:.0f}분/일 — 기준 {t['max_total_min']}분 초과")

    # ② 오락 카테고리 비중 점수 (0~30점)
    ent_vals = []
    for d in dates:
        rec = daily_records.get(d, {})
        sc = rec.get("screentime")
        if not isinstance(sc, dict):
            continue
        by_cat = sc.get("by_category", {})
        if not isinstance(by_cat, dict):
            continue
        ent_min = sum(
            float(v)
            for k, v in by_cat.items()
            if k in t["ent_categories"] and isinstance(v, (int, float))
        )
        ent_vals.append(ent_min)

    avg_ent = statistics.mean(ent_vals) if ent_vals else 0.0

    if avg_ent <= t["max_ent_min"]:
        ent_score = 30.0
    else:
        over = avg_ent - t["max_ent_min"]
        ent_score = _clamp(30 - (over / 30) * 10)
        flags.append(f"오락 앱 {avg_ent:.0f}분/일 — 기준 {t['max_ent_min']}분 초과")

    detail = {
        "avg_daily_min": avg_min,
        "avg_ent_min":   round(avg_ent, 1),
        "vs_baseline":   ws.get("screentime", {}).get("vs_baseline"),
    }
    return _clamp(total_score + ent_score), flags, detail


def _score_spending(
    ws: dict,
    daily_records: dict,
    dates: List[str],
) -> Tuple[float, List[str], dict]:
    """
    ws["finance"] = { total_spent_week }
    daily_records["finance"]["total_spent"] → 집중도(top1_ratio) 직접 계산
    evidence.py의 IQR 이상치 로직과 동일 방식으로 집중도 페널티 적용
    """
    flags: List[str] = []
    t = THR["spending"]

    total_raw = ws.get("finance", {}).get("total_spent_week")
    if total_raw is None:
        return 0.0, ["소비 데이터 없음"], {"total_spent_week": None}

    total_week = float(total_raw)

    # ① 주간 총액 점수 (0~75점)
    if total_week <= t["ideal_weekly"]:
        amount_score = 75.0
    elif total_week <= t["limit_weekly"]:
        ratio = (total_week - t["ideal_weekly"]) / (t["limit_weekly"] - t["ideal_weekly"])
        amount_score = 75 - ratio * 37.5
    else:
        over = total_week - t["limit_weekly"]
        amount_score = _clamp(37.5 - (over / t["limit_weekly"]) * 37.5)
        flags.append(
            f"주간 소비 {total_week:,.0f}원 — 기준 {t['limit_weekly']:,.0f}원 초과"
        )

    # ② 지출 집중도 페널티 (최대 -25점)
    # evidence.py _iqr_outlier_days 와 동일: 이상치 날짜 제외 후 집중도 계산
    spend_by_date = {}
    for d in dates:
        rec = daily_records.get(d, {})
        fin = rec.get("finance")
        if isinstance(fin, dict) and fin.get("total_spent") is not None:
            spend_by_date[d] = float(fin["total_spent"])

    concentration_penalty = 0.0
    top1_ratio = None
    top1_ratio_adj = None

    if spend_by_date:
        spend_sum = sum(spend_by_date.values())
        if spend_sum > 0:
            top1_day = max(spend_by_date, key=spend_by_date.get)
            top1 = spend_by_date[top1_day]
            top1_ratio = top1 / spend_sum

            # IQR 이상치 제거 후 재계산 (evidence.py 방식 동일)
            vals = list(spend_by_date.values())
            if len(vals) >= 4:
                vals_sorted = sorted(vals)
                q1 = statistics.median(vals_sorted[:len(vals_sorted)//2])
                q3 = statistics.median(vals_sorted[(len(vals_sorted)+1)//2:])
                iqr = q3 - q1
                lo, hi = q1 - 1.5*iqr, q3 + 1.5*iqr
                adj = {d: v for d, v in spend_by_date.items() if lo <= v <= hi}
            else:
                adj = spend_by_date

            if adj and sum(adj.values()) > 0:
                adj_sum = sum(adj.values())
                adj_top1 = max(adj.values())
                top1_ratio_adj = adj_top1 / adj_sum

            # 집중도 페널티: 이상치 제거 후 값 기준 적용
            effective_ratio = top1_ratio_adj if top1_ratio_adj is not None else top1_ratio
            if effective_ratio >= t["top1_penalty_thr"]:
                concentration_penalty = _clamp(
                    (effective_ratio - t["top1_penalty_thr"]) / 0.20 * 25, 0, 25
                )
                outlier_note = " (이상치 제거 후)" if top1_ratio_adj is not None else ""
                flags.append(
                    f"지출 집중도 높음 — 최고 지출일 비중 {effective_ratio:.1%}{outlier_note} "
                    f"(기준 {t['top1_penalty_thr']:.0%} 이상)"
                )

    detail = {
        "total_spent_week": int(total_week),
        "daily_avg":        round(total_week / len(dates), 0) if dates else None,
        "top1_ratio":       round(top1_ratio, 3)     if top1_ratio     is not None else None,
        "top1_ratio_adj":   round(top1_ratio_adj, 3) if top1_ratio_adj is not None else None,
    }
    return _clamp(amount_score - concentration_penalty), flags, detail


# ── 메인 계산 함수 ─────────────────────────────────────────────────────────────

def calculate_scores(
    week: str,
    weekly_summary_entry: dict,
    daily_records: dict,
) -> WeeklyScore:
    """
    Parameters
    ----------
    week : str
        "2025-W47"
    weekly_summary_entry : dict
        weekly_summary.json[week]  — build_weekly_summary() 반환값
    daily_records : dict
        daily_records.json 전체  — {"2025-11-26": {...}, ...}
    """
    ws = weekly_summary_entry

    # 해당 주 날짜 범위 추출
    date_range = ws.get("date_range", "")
    if " ~ " in date_range:
        start_str, end_str = date_range.split(" ~ ")
        dates = [d for d in sorted(daily_records.keys()) if start_str <= d <= end_str]
    else:
        dates = []

    results = [
        ("sleep",      _score_sleep(ws, daily_records, dates)),
        ("steps",      _score_steps(ws)),
        ("screentime", _score_screentime(ws, daily_records, dates)),
        ("spending",   _score_spending(ws, daily_records, dates)),
    ]

    items: Dict[str, ItemScore] = {}
    total = 0.0
    for cat, (raw, flags, detail) in results:
        w = WEIGHTS[cat]
        weighted = raw * w / 100
        total += weighted
        items[cat] = ItemScore(
            category=cat,
            raw_score=round(raw, 1),
            weighted=round(weighted, 2),
            grade=_grade(raw),
            weight=w,
            detail=detail,
            flags=flags,
        )

    total = round(_clamp(total), 1)
    grade = _grade(total)

    return WeeklyScore(
        week=week,
        total=total,
        grade=grade,
        items=items,
        summary_line=_make_summary_line(week, total, grade, items),
        score_block=_make_score_block(week, total, grade, items),
    )


# ── 포매터 ────────────────────────────────────────────────────────────────────

def _make_summary_line(week: str, total: float, grade: str, items: dict) -> str:
    parts = " | ".join(
        f"{KO[c]} {s.raw_score:.0f}점({s.grade})"
        for c, s in items.items()
    )
    return f"[{week}] 종합 {total:.1f}점 ({grade}) — {parts}"


def _make_score_block(week: str, total: float, grade: str, items: dict) -> str:
    W = 54
    sep = "=" * W
    sub = "-" * W
    lines = [
        sep,
        f"  주간 건강 점수   {week}",
        sep,
        f"  종합 점수 : {total:.1f} / 100     등급 : {grade}",
        f"  {_bar(total, 32)}",
        sub,
    ]
    for cat, s in items.items():
        lines.append(
            f"  {KO[cat]:<8}  {s.raw_score:5.1f}점  {s.grade}  "
            f"{_bar(s.raw_score, 20)}  (배점 {s.weight}점)"
        )
        for flag in s.flags:
            lines.append(f"           ※ {flag}")
    lines += [
        sub,
        "  배점 기준: 수면 30 · 활동 25 · 스크린 25 · 소비 20",
        sep,
    ]
    return "\n".join(lines)


# ── JSON 직렬화 (시각화용) ────────────────────────────────────────────────────

def to_score_json(ws: WeeklyScore) -> dict:
    """
    반환 구조
    {
      week, total, grade, summary,
      radar: [{category, key, score, grade, weight, flags, detail}, ...],
      bar:   [{label, value}, ...]
    }
    Chart.js radar / Recharts Bar / D3 에 바로 사용 가능
    """
    return {
        "week":    ws.week,
        "total":   ws.total,
        "grade":   ws.grade,
        "summary": ws.summary_line,
        "radar": [
            {
                "category": KO[cat],
                "key":      cat,
                "score":    s.raw_score,
                "grade":    s.grade,
                "weight":   s.weight,
                "flags":    s.flags,
                "detail":   s.detail,
            }
            for cat, s in ws.items.items()
        ],
        "bar": [
            {"label": KO[cat], "value": s.raw_score}
            for cat, s in ws.items.items()
        ],
    }
