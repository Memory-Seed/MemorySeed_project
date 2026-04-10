# src/model/evidence.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
import math
import statistics


# -----------------------------
# Helpers: numeric safety
# -----------------------------
def _to_float(x: Any) -> Optional[float]:
    if x is None:
        return None
    if isinstance(x, bool):
        return None
    if isinstance(x, (int, float)):
        xf = float(x)
        if math.isnan(xf):
            return None
        return xf
    return None


def _clean(xs: List[Optional[float]]) -> List[float]:
    out: List[float] = []
    for x in xs:
        if x is None:
            continue
        try:
            xf = float(x)
        except Exception:
            continue
        if math.isnan(xf):
            continue
        out.append(xf)
    return out


def _mean(xs: List[Optional[float]]) -> Optional[float]:
    vals = _clean(xs)
    return statistics.mean(vals) if vals else None


def _median(xs: List[Optional[float]]) -> Optional[float]:
    vals = _clean(xs)
    return statistics.median(vals) if vals else None


def _stdev(xs: List[Optional[float]]) -> Optional[float]:
    vals = _clean(xs)
    return statistics.stdev(vals) if len(vals) >= 2 else None


def _rng(xs: List[Optional[float]]) -> Optional[float]:
    vals = _clean(xs)
    return (max(vals) - min(vals)) if vals else None


def _pearson_corr(xs: List[Optional[float]], ys: List[Optional[float]]) -> Optional[float]:
    pairs: List[Tuple[float, float]] = []
    for x, y in zip(xs, ys):
        if x is None or y is None:
            continue
        try:
            xf = float(x)
            yf = float(y)
        except Exception:
            continue
        if math.isnan(xf) or math.isnan(yf):
            continue
        pairs.append((xf, yf))

    if len(pairs) < 3:
        return None

    xvals = [p[0] for p in pairs]
    yvals = [p[1] for p in pairs]
    mx = statistics.mean(xvals)
    my = statistics.mean(yvals)

    num = sum((x - mx) * (y - my) for x, y in pairs)
    denx = math.sqrt(sum((x - mx) ** 2 for x in xvals))
    deny = math.sqrt(sum((y - my) ** 2 for y in yvals))
    if denx == 0 or deny == 0:
        return None
    return num / (denx * deny)


def _corr_label(r: Optional[float]) -> str:
    if r is None:
        return "insufficient"
    a = abs(r)
    if a < 0.30:
        return "none"
    if a < 0.50:
        return "weak"
    if a < 0.70:
        return "moderate"
    return "strong"


def _argmax(arr: List[Optional[float]]) -> Optional[int]:
    vals = [(i, x) for i, x in enumerate(arr) if x is not None]
    return max(vals, key=lambda t: t[1])[0] if vals else None


def _argmin(arr: List[Optional[float]]) -> Optional[int]:
    vals = [(i, x) for i, x in enumerate(arr) if x is not None]
    return min(vals, key=lambda t: t[1])[0] if vals else None


def _top_k_sum(d: Dict[str, float], k: int = 3) -> List[Tuple[str, float]]:
    return sorted(d.items(), key=lambda t: t[1], reverse=True)[:k]


def _iqr_bounds(values: List[Optional[float]]) -> Tuple[float, float]:
    """IQR 기준 하한/상한 반환 (lo, hi)"""
    vals = sorted(_clean(values))
    if len(vals) < 4:
        return (-math.inf, math.inf)
    q1 = statistics.median(vals[:len(vals) // 2])
    q3 = statistics.median(vals[(len(vals) + 1) // 2:])
    iqr = q3 - q1
    return q1 - 1.5 * iqr, q3 + 1.5 * iqr


def _iqr_outlier_days(values: List[Optional[float]], dates: List[str]) -> List[str]:
    vals = _clean(values)
    if len(vals) < 4:
        return []

    lo, hi = _iqr_bounds(values)
    out: List[str] = []
    for i, x in enumerate(values):
        if x is None:
            continue
        if x < lo or x > hi:
            out.append(dates[i])
    return out


def _spend_adjusted(
    spend: List[Optional[float]],
    dates: List[str],
) -> Tuple[List[Optional[float]], List[str]]:
    """
    IQR 이상치 날짜를 제거한 spend 리스트와 해당 날짜 리스트 반환.
    이상치 없으면 원본 그대로 반환.
    """
    lo, hi = _iqr_bounds(spend)
    adj_spend: List[Optional[float]] = []
    adj_dates: List[str] = []
    for d, v in zip(dates, spend):
        if v is None:
            continue
        if lo <= v <= hi:
            adj_spend.append(v)
            adj_dates.append(d)
    return adj_spend, adj_dates


# -----------------------------
# Row extraction for your data schema
# -----------------------------
@dataclass
class DayRow:
    date: str
    sleep_h: Optional[float]
    steps: Optional[float]
    screen_min: Optional[float]
    spend_krw: Optional[float]
    weather_cond: str
    weather_avg_temp: Optional[float]
    events_total: float
    events_total_min: float
    events_by_cat: Dict[str, int]


def _extract_day_row(date_str: str, rec: Dict[str, Any]) -> DayRow:
    # sleep
    sleep_h = None
    sleep = rec.get("sleep")
    if isinstance(sleep, dict):
        sleep_h = _to_float(sleep.get("duration_hours"))

    # steps
    steps = None
    st = rec.get("steps")
    if isinstance(st, dict):
        steps = _to_float(st.get("total_steps"))
    if steps is None:
        steps = _to_float(rec.get("steps"))

    # screentime
    screen_min = None
    st2 = rec.get("screentime")
    if isinstance(st2, dict):
        screen_min = _to_float(st2.get("total_min"))

    # weather
    weather_cond = "unknown"
    weather_avg_temp = None
    w = rec.get("weather")
    if isinstance(w, dict):
        c = w.get("condition")
        if isinstance(c, str) and c.strip():
            weather_cond = c.strip()
        weather_avg_temp = _to_float(w.get("avg_temp"))

    # finance
    spend_krw = None
    fin = rec.get("finance")
    if isinstance(fin, dict):
        spend_krw = _to_float(fin.get("total_spent"))

    # calendar
    events_by_cat: Dict[str, int] = {}
    events_total = 0
    events_total_min = 0
    cal = rec.get("calendar")
    if isinstance(cal, list):
        for ev in cal:
            if not isinstance(ev, dict):
                continue
            cat = ev.get("category") or "unknown"
            if not isinstance(cat, str):
                cat = "unknown"
            cat = cat.strip() if cat.strip() else "unknown"
            events_by_cat[cat] = events_by_cat.get(cat, 0) + 1
            events_total += 1

            dur = ev.get("duration_min")
            if isinstance(dur, (int, float)) and not isinstance(dur, bool):
                events_total_min += int(dur)

    return DayRow(
        date=date_str,
        sleep_h=sleep_h,
        steps=steps,
        screen_min=screen_min,
        spend_krw=spend_krw,
        weather_cond=weather_cond,
        weather_avg_temp=weather_avg_temp,
        events_total=float(events_total),
        events_total_min=float(events_total_min),
        events_by_cat=events_by_cat,
    )


# -----------------------------
# Main API: build_week_evidence
# -----------------------------
def build_week_evidence(
    daily_records: Dict[str, Any],
    start_str: str,
    end_str: str,
    baseline: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Called from run_llm_analysis.py:
        evidence_block = build_week_evidence(daily_records, start_str, end_str, baseline)

    Produces a numeric Evidence Block for LLM grounding.
    """

    # 1) Filter dates
    dates = [d for d in sorted(daily_records.keys()) if start_str <= d <= end_str]
    if not dates:
        return "[Evidence Block]\n- no daily records in this range"

    # 2) Extract rows (stable schema)
    rows: List[DayRow] = []
    for d in dates:
        rec = daily_records[d]
        if not isinstance(rec, dict):
            continue
        rows.append(_extract_day_row(d, rec))

    if not rows:
        return "[Evidence Block]\n- no valid daily records in this range"

    # 3) Prepare lines
    lines: List[str] = []
    lines.append("[Evidence Block]")
    lines.append(f"- date_range={start_str} ~ {end_str} (days={len(rows)})")

    # 4) Collect series
    sleep        = [r.sleep_h       for r in rows]
    steps        = [r.steps         for r in rows]
    screen       = [r.screen_min    for r in rows]
    spend        = [r.spend_krw     for r in rows]
    events_total = [r.events_total  for r in rows]
    temp         = [r.weather_avg_temp for r in rows]

    # 5) Data quality notes
    quality_notes: List[str] = []
    for name, arr in [("sleep_h", sleep), ("steps", steps), ("screen_min", screen), ("spend_krw", spend)]:
        miss = sum(1 for x in arr if x is None)
        if miss:
            quality_notes.append(f"{name} missing: {miss} day(s)")

    spend_out_days = _iqr_outlier_days(spend, [r.date for r in rows])
    if spend_out_days:
        quality_notes.append("spend_krw outlier day(s): " + ", ".join(spend_out_days))

    # 6) Stats summary
    stats = {
        "sleep_mean":   _mean(sleep),
        "sleep_median": _median(sleep),
        "sleep_std":    _stdev(sleep),
        "sleep_range":  _rng(sleep),

        "steps_mean":   _mean(steps),
        "steps_median": _median(steps),
        "steps_std":    _stdev(steps),
        "steps_range":  _rng(steps),

        "screen_mean":   _mean(screen),
        "screen_median": _median(screen),
        "screen_std":    _stdev(screen),
        "screen_range":  _rng(screen),

        "spend_sum":    sum(_clean(spend)),
        "spend_mean":   _mean(spend),
        "spend_median": _median(spend),
        "spend_std":    _stdev(spend),
        "spend_range":  _rng(spend),
    }

    # ── ③ 이상치 제거 후 보정 spend 통계 ────────────────────────────────────
    adj_spend, adj_dates = _spend_adjusted(spend, [r.date for r in rows])
    has_outlier = len(adj_spend) < len(_clean(spend))

    adj_stats = {
        "spend_adj_mean":   _mean(adj_spend)   if adj_spend else None,
        "spend_adj_median": _median(adj_spend) if adj_spend else None,
        "spend_adj_std":    _stdev(adj_spend)  if adj_spend else None,
        "spend_adj_n":      len(adj_spend),
    }

    # 7) Extremes
    max_sleep_i, min_sleep_i   = _argmax(sleep),  _argmin(sleep)
    max_screen_i, min_screen_i = _argmax(screen), _argmin(screen)
    max_spend_i, min_spend_i   = _argmax(spend),  _argmin(spend)

    # 8) Spending concentration (원본 + 이상치 제거 후 비교)
    spend_vals = sorted(_clean(spend), reverse=True)
    spend_sum  = stats["spend_sum"] or 0.0
    top1  = spend_vals[0]              if len(spend_vals) >= 1 else 0.0
    top2  = sum(spend_vals[:2])        if len(spend_vals) >= 2 else top1
    top1_ratio = (top1 / spend_sum)    if spend_sum > 0 else None
    top2_ratio = (top2 / spend_sum)    if spend_sum > 0 else None

    # 이상치 제거 후 집중도
    adj_spend_vals = sorted(_clean(adj_spend), reverse=True)
    adj_sum        = sum(adj_spend_vals) if adj_spend_vals else 0.0
    adj_top1       = adj_spend_vals[0]         if len(adj_spend_vals) >= 1 else 0.0
    adj_top2       = sum(adj_spend_vals[:2])   if len(adj_spend_vals) >= 2 else adj_top1
    adj_top1_ratio = (adj_top1 / adj_sum)      if adj_sum > 0 else None
    adj_top2_ratio = (adj_top2 / adj_sum)      if adj_sum > 0 else None

    # 9) Correlations — 확장: sleep↔spend, sleep↔temp, screen↔steps 추가
    corr_sleep_screen = _pearson_corr(sleep, screen)
    corr_events_sleep = _pearson_corr(events_total, sleep)
    corr_sleep_spend  = _pearson_corr(sleep, spend)
    corr_sleep_temp   = _pearson_corr(sleep, temp)
    corr_screen_steps = _pearson_corr(screen, steps)
    corr_screen_spend = _pearson_corr(screen, spend)

    # 이상치 제거 후 sleep↔spend 재계산
    corr_sleep_spend_adj: Optional[float] = None
    if adj_spend and len(adj_dates) >= 3:
        sleep_adj = [r.sleep_h for r in rows if r.date in set(adj_dates)]
        corr_sleep_spend_adj = _pearson_corr(sleep_adj, adj_spend)

    # 10) Weather vs steps mean by condition
    weather_groups: Dict[str, List[float]] = {}
    for r in rows:
        if r.steps is None:
            continue
        weather_groups.setdefault(r.weather_cond, []).append(float(r.steps))
    weather_means = {k: (statistics.mean(v) if v else None) for k, v in weather_groups.items()}

    # 11) Top spending days
    spend_rank = sorted(
        [(i, spend[i]) for i in range(len(spend)) if spend[i] is not None],
        key=lambda t: t[1],
        reverse=True
    )[:3]
    top_spend_lines: List[str] = []
    for i, amt in spend_rank:
        cats = rows[i].events_by_cat
        top_cats = sorted(cats.items(), key=lambda t: t[1], reverse=True)[:2]
        cat_str = ", ".join(f"{k}:{v}" for k, v in top_cats) if top_cats else "calendar:none"
        is_out = rows[i].date in spend_out_days
        out_tag = " [OUTLIER]" if is_out else ""
        top_spend_lines.append(f"  - {rows[i].date}: {int(amt):,} KRW ({cat_str}){out_tag}")

    # 12) Deep drivers
    screen_cat_sum: Dict[str, float]    = {}
    app_sum: Dict[str, float]           = {}
    spend_cat_sum: Dict[str, float]     = {}
    spend_merchant_sum: Dict[str, float]= {}
    cal_cat_count: Dict[str, int]       = {}
    cal_cat_min_sum: Dict[str, int]     = {}

    for d in dates:
        rec = daily_records.get(d)
        if not isinstance(rec, dict):
            continue

        st2 = rec.get("screentime")
        if isinstance(st2, dict):
            bc = st2.get("by_category")
            if isinstance(bc, dict):
                for k, v in bc.items():
                    if isinstance(v, (int, float)) and not isinstance(v, bool):
                        key = str(k)
                        screen_cat_sum[key] = screen_cat_sum.get(key, 0.0) + float(v)
            ta = st2.get("top_apps")
            if isinstance(ta, list):
                for item in ta:
                    if not isinstance(item, dict):
                        continue
                    app  = item.get("app")
                    mins = item.get("min")
                    if isinstance(app, str) and isinstance(mins, (int, float)) and not isinstance(mins, bool):
                        app_sum[app] = app_sum.get(app, 0.0) + float(mins)

        fin = rec.get("finance")
        if isinstance(fin, dict):
            txs = fin.get("transactions")
            if isinstance(txs, list):
                for t in txs:
                    if not isinstance(t, dict):
                        continue
                    if str(t.get("type")) != "출금":
                        continue
                    amt = t.get("amount")
                    if not isinstance(amt, (int, float)) or isinstance(amt, bool):
                        continue
                    cat = str(t.get("category") or "unknown")
                    mer = str(t.get("merchant") or "unknown")
                    spend_cat_sum[cat]      = spend_cat_sum.get(cat, 0.0)      + float(amt)
                    spend_merchant_sum[mer] = spend_merchant_sum.get(mer, 0.0) + float(amt)

        cal = rec.get("calendar")
        if isinstance(cal, list):
            for ev in cal:
                if not isinstance(ev, dict):
                    continue
                cat = str(ev.get("category") or "unknown").strip() or "unknown"
                cal_cat_count[cat]   = cal_cat_count.get(cat, 0) + 1
                dur = ev.get("duration_min")
                if isinstance(dur, (int, float)) and not isinstance(dur, bool):
                    cal_cat_min_sum[cat] = cal_cat_min_sum.get(cat, 0) + int(dur)

    screen_total = sum(screen_cat_sum.values()) or 0.0
    spend_total  = sum(spend_cat_sum.values())  or 0.0

    top_screen_cats = _top_k_sum(screen_cat_sum, 3)
    top_apps        = _top_k_sum(app_sum, 3)
    top_spend_cats  = _top_k_sum(spend_cat_sum, 3)
    top_merchants   = _top_k_sum(spend_merchant_sum, 3)

    top_cal_by_count   = sorted(cal_cat_count.items(),   key=lambda t: t[1], reverse=True)[:3]
    top_cal_by_minutes = sorted(cal_cat_min_sum.items(), key=lambda t: t[1], reverse=True)[:3]

    # 13) Risk flags
    risk_flags: List[str] = []
    if stats["sleep_range"] is not None and stats["sleep_range"] > 5.0:
        risk_flags.append("sleep_instability_high")
    if top2_ratio is not None and top2_ratio > 0.60:
        # 이상치 제거 후에도 high인지 체크
        if adj_top2_ratio is not None and adj_top2_ratio > 0.60:
            risk_flags.append("spending_concentration_high")
        else:
            risk_flags.append("spending_concentration_high_outlier_driven")
    if stats["screen_mean"] is not None and stats["screen_mean"] > 420.0:
        risk_flags.append("screen_overuse_risk")

    # ── Emit ─────────────────────────────────────────────────────────────────

    # 14) Core stats
    if stats["sleep_mean"] is not None:
        lines.append(
            f"- sleep_mean={stats['sleep_mean']:.2f}h, sleep_median={stats['sleep_median']:.2f}h, "
            f"sleep_std={stats['sleep_std']:.2f}h, sleep_range={stats['sleep_range']:.2f}h"
        )
    else:
        lines.append("- sleep: n/a")

    if stats["steps_mean"] is not None:
        lines.append(
            f"- steps_mean={stats['steps_mean']:.0f}, steps_median={stats['steps_median']:.0f}, "
            f"steps_std={stats['steps_std']:.0f}, steps_range={stats['steps_range']:.0f}"
        )
    else:
        lines.append("- steps: n/a")

    if stats["screen_mean"] is not None:
        lines.append(
            f"- screen_mean={stats['screen_mean']:.1f}min, screen_median={stats['screen_median']:.1f}min, "
            f"screen_std={stats['screen_std']:.1f}min, screen_range={stats['screen_range']:.1f}min"
        )
    else:
        lines.append("- screen: n/a")

    if stats["spend_mean"] is not None:
        lines.append(
            f"- spend_sum={int(stats['spend_sum']):,} KRW, "
            f"spend_mean={stats['spend_mean']:.0f}, spend_median={stats['spend_median']:.0f}, "
            f"spend_std={stats['spend_std']:.0f}"
        )
    else:
        lines.append("- spend: n/a")

    # ── ③ 이상치 제거 후 보정 spend 통계 출력 ────────────────────────────────
    if has_outlier and adj_stats["spend_adj_mean"] is not None:
        lines.append(
            f"- spend_adj(outlier_removed, n={adj_stats['spend_adj_n']}): "
            f"mean={adj_stats['spend_adj_mean']:.0f}, "
            f"median={adj_stats['spend_adj_median']:.0f}, "
            f"std={adj_stats['spend_adj_std']:.0f}"
        )
        lines.append(
            f"  ※ 이상치 날짜({', '.join(spend_out_days)}) 제외 후 보정값. "
            f"지출 해석 시 spend_adj 값을 대표값으로 권장."
        )

    # 15) Extremes
    lines.append("- extremes:")
    if max_sleep_i is not None and min_sleep_i is not None:
        lines.append(
            f"  - sleep_max={rows[max_sleep_i].date} ({sleep[max_sleep_i]:.2f}h), "
            f"sleep_min={rows[min_sleep_i].date} ({sleep[min_sleep_i]:.2f}h)"
        )
    if max_screen_i is not None and min_screen_i is not None:
        lines.append(
            f"  - screen_max={rows[max_screen_i].date} ({screen[max_screen_i]:.1f}m), "
            f"screen_min={rows[min_screen_i].date} ({screen[min_screen_i]:.1f}m)"
        )
    if max_spend_i is not None and min_spend_i is not None:
        out_tag = " [OUTLIER]" if rows[max_spend_i].date in spend_out_days else ""
        lines.append(
            f"  - spend_max={rows[max_spend_i].date} ({int(spend[max_spend_i]):,} KRW){out_tag}, "
            f"spend_min={rows[min_spend_i].date} ({int(spend[min_spend_i]):,} KRW)"
        )

    # 16) Spending concentration (원본 + 보정)
    if top1_ratio is not None and top2_ratio is not None:
        lines.append(f"- spend_top1_ratio={top1_ratio:.2%}, spend_top2_ratio={top2_ratio:.2%}")
        if has_outlier and adj_top1_ratio is not None:
            lines.append(
                f"- spend_adj_top1_ratio={adj_top1_ratio:.2%}, "
                f"spend_adj_top2_ratio={adj_top2_ratio:.2%}  ※ 이상치 제거 후"
            )
    else:
        lines.append("- spend_top1_ratio=n/a, spend_top2_ratio=n/a")

    # 17) Correlations — 확장 출력
    lines.append("- correlations:")
    for label, val in [
        ("corr(sleep_h, screen_min)",     corr_sleep_screen),
        ("corr(sleep_h, spend_krw)",      corr_sleep_spend),
        ("corr(sleep_h, spend_krw)_adj",  corr_sleep_spend_adj),
        ("corr(sleep_h, avg_temp)",       corr_sleep_temp),
        ("corr(screen_min, steps)",       corr_screen_steps),
        ("corr(screen_min, spend_krw)",   corr_screen_spend),
        ("corr(events_total, sleep_h)",   corr_events_sleep),
    ]:
        if val is not None:
            lbl = _corr_label(val)
            usable = "" if lbl in ("none", "insufficient") else "  ← 해석 가능"
            lines.append(f"  - {label}={val:.3f} ({lbl}){usable}")
        else:
            lines.append(f"  - {label}=n/a (insufficient)")

    if weather_means:
        wm = ", ".join(f"{k}:{(v or 0):.0f}" for k, v in sorted(weather_means.items()))
        lines.append(f"- mean_steps_by_weather={wm}")
    else:
        lines.append("- mean_steps_by_weather=n/a")

    # 18) Top days spend
    lines.append("- spending_top_days:")
    if top_spend_lines:
        lines.extend(top_spend_lines)
    else:
        lines.append("  - n/a")

    # 19) Screen drivers
    lines.append("- screen_top_categories:")
    if top_screen_cats:
        for k, v in top_screen_cats:
            ratio = (v / screen_total) if screen_total > 0 else 0.0
            lines.append(f"  - {k}: {v:.0f} min ({ratio:.1%})")
    else:
        lines.append("  - n/a")

    lines.append("- screen_top_apps:")
    if top_apps:
        for k, v in top_apps:
            lines.append(f"  - {k}: {v:.0f} min")
    else:
        lines.append("  - n/a")

    # 20) Spend drivers
    lines.append("- spend_top_categories:")
    if top_spend_cats:
        for k, v in top_spend_cats:
            ratio = (v / spend_total) if spend_total > 0 else 0.0
            lines.append(f"  - {k}: {int(v):,} KRW ({ratio:.1%})")
    else:
        lines.append("  - n/a")

    lines.append("- spend_top_merchants:")
    if top_merchants:
        for k, v in top_merchants:
            lines.append(f"  - {k}: {int(v):,} KRW")
    else:
        lines.append("  - n/a")

    # 21) Calendar load
    lines.append("- calendar_load_top_by_count:")
    if top_cal_by_count:
        for k, v in top_cal_by_count:
            lines.append(f"  - {k}: {v} events")
    else:
        lines.append("  - n/a")

    lines.append("- calendar_load_top_by_minutes:")
    if top_cal_by_minutes:
        for k, v in top_cal_by_minutes:
            lines.append(f"  - {k}: {v} min")
    else:
        lines.append("  - n/a")

    # 22) Risk flags
    lines.append(f"- risk_flags={risk_flags}")

    # 23) Data quality
    if quality_notes:
        lines.append("[Data Quality Notes]")
        for n in quality_notes:
            lines.append(f"- {n}")

    return "\n".join(lines)