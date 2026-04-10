"""
build_llm_input_summary.py — 전처리 데이터 → LLM 입력용 자연어 요약 생성
"""

from collections import defaultdict
from datetime import datetime

from src.utils.helpers import get_weekday_kr


# ── 베이스라인 계산 ───────────────────────────────────────────────────────────

def compute_baseline(daily_records: dict) -> dict:
    """전체 기간 데이터 기반 개인 평균(베이스라인) 계산"""
    sleep_hours, steps_list, screen_list = [], [], []

    for rec in daily_records.values():
        if rec.get("sleep"):
            sleep_hours.append(rec["sleep"]["duration_hours"])
        if rec.get("steps"):
            steps_list.append(rec["steps"]["total_steps"])
        if rec.get("screentime"):
            screen_list.append(rec["screentime"]["total_min"])

    def avg(lst):
        return round(sum(lst) / len(lst), 1) if lst else 0

    return {
        "avg_sleep_hours":    avg(sleep_hours),
        "avg_steps":          int(avg(steps_list)),
        "avg_screentime_min": avg(screen_list),
    }


# ── 일별 통합 레코드 구성 ─────────────────────────────────────────────────────

def build_daily_records(sleep, steps, screentime, weather, calendar, notification) -> dict:
    """모든 도메인을 날짜 키 기준으로 통합"""
    all_dates = set()
    for d in [sleep, steps, screentime, weather, calendar, notification]:
        all_dates.update(d.keys())

    return {
        date: {
            "date":       date,
            "sleep":      sleep.get(date),
            "steps":      steps.get(date),
            "screentime": screentime.get(date),
            "weather":    weather.get(date),
            "calendar":   calendar.get(date, []),
            "finance":    notification.get(date),
        }
        for date in sorted(all_dates)
    }


# ── 주별 요약 생성 ────────────────────────────────────────────────────────────

def build_weekly_summary(daily_records: dict, baseline: dict) -> dict:
    """일별 레코드를 ISO 주차 기준으로 묶어 주별 요약 생성"""
    weekly = defaultdict(list)
    for date_str, rec in daily_records.items():
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        weekly[dt.strftime("%Y-W%W")].append(rec)

    def w_avg(vals):
        return round(sum(vals) / len(vals), 1) if vals else None

    def w_sum(vals):
        return sum(vals) if vals else 0

    summaries = {}
    for week_key, recs in sorted(weekly.items()):
        dates       = [r["date"] for r in recs]
        sleep_vals  = [r["sleep"]["duration_hours"] for r in recs if r.get("sleep")]
        steps_vals  = [r["steps"]["total_steps"]    for r in recs if r.get("steps")]
        screen_vals = [r["screentime"]["total_min"] for r in recs if r.get("screentime")]
        spend_vals  = [r["finance"]["total_spent"]  for r in recs if r.get("finance")]
        all_events  = [e for r in recs for e in r.get("calendar", [])]
        conditions  = [r["weather"]["condition"] for r in recs if r.get("weather")]
        avg_temps   = [r["weather"]["avg_temp"]   for r in recs if r.get("weather")]

        avg_sleep  = w_avg(sleep_vals)
        avg_steps  = w_avg(steps_vals)
        avg_screen = w_avg(screen_vals)

        summaries[week_key] = {
            "week":          week_key,
            "date_range":    f"{dates[0]} ~ {dates[-1]}",
            "days_recorded": len(dates),
            "sleep": {
                "avg_hours":   avg_sleep,
                "vs_baseline": round(avg_sleep - baseline["avg_sleep_hours"], 1)
                               if avg_sleep else None,
            },
            "steps": {
                "avg_daily":   int(avg_steps) if avg_steps else None,
                "vs_baseline": int(avg_steps - baseline["avg_steps"])
                               if avg_steps else None,
            },
            "screentime": {
                "avg_daily_min": avg_screen,
                "vs_baseline":   round(avg_screen - baseline["avg_screentime_min"], 1)
                                 if avg_screen else None,
            },
            "finance": {
                "total_spent_week": w_sum(spend_vals),
            },
            "weather": {
                "main_condition": max(set(conditions), key=conditions.count)
                                  if conditions else None,
                "avg_temp":       round(sum(avg_temps) / len(avg_temps), 1)
                                  if avg_temps else None,
            },
            "calendar": {
                "total_events": len(all_events),
                "categories":   list(set(e["category"] for e in all_events)),
            },
        }

    return summaries


# ── 일별 자연어 요약 ──────────────────────────────────────────────────────────

def format_daily_summary(rec: dict, baseline: dict) -> str:
    """일별 레코드 → LLM 입력용 자연어 요약 텍스트"""
    date_str = rec["date"]
    weekday  = get_weekday_kr(date_str)
    lines    = [f"[{date_str} ({weekday}요일)]"]

    # 수면
    if rec.get("sleep"):
        s    = rec["sleep"]
        diff = round(s["duration_hours"] - baseline["avg_sleep_hours"], 1)
        sign = "+" if diff >= 0 else ""
        note = f" [{s['note']}]" if s.get("note") else ""
        lines.append(
            f"😴 수면: {s['bedtime']} 취침 → {s['wakeup']} 기상 | "
            f"{s['duration_hours']}시간 (평균 대비 {sign}{diff}h){note}"
        )
    else:
        lines.append("😴 수면: 데이터 없음")

    # 걸음수
    if rec.get("steps"):
        st   = rec["steps"]
        diff = st["total_steps"] - baseline["avg_steps"]
        sign = "+" if diff >= 0 else ""
        lines.append(f"🚶 걸음수: {st['total_steps']:,}보 (평균 대비 {sign}{diff:,}보)")
    else:
        lines.append("🚶 걸음수: 데이터 없음")

    # 스크린타임
    if rec.get("screentime"):
        sc   = rec["screentime"]
        diff = round(sc["total_min"] - baseline["avg_screentime_min"], 1)
        sign = "+" if diff >= 0 else ""
        cat_str = " / ".join(f"{k} {round(v)}분" for k, v in sc["by_category"].items())
        top_str = ", ".join(f"{a['app']}({round(a['min'])}분)" for a in sc["top_apps"])
        lines.append(
            f"📱 스크린타임: 총 {round(sc['total_min'])}분 (평균 대비 {sign}{diff}분) | "
            f"카테고리: {cat_str} | TOP: {top_str}"
        )
    else:
        lines.append("📱 스크린타임: 데이터 없음")

    # 날씨
    if rec.get("weather"):
        w = rec["weather"]
        lines.append(
            f"🌤️ 날씨: {w['condition']}, 평균 {w['avg_temp']}°C "
            f"(체감 {w['avg_feel_temp']}°C), 강수확률 {w['precip_prob']}%, 습도 {w['avg_humidity']}%"
        )
    else:
        lines.append("🌤️ 날씨: 데이터 없음")

    # 캘린더
    if rec.get("calendar"):
        ev_strs = [f"{e['summary']}({e['start']}~{e['end']})" for e in rec["calendar"]]
        lines.append(f"📅 일정: {' / '.join(ev_strs)}")
    else:
        lines.append("📅 일정: 없음")

    # 금융
    if rec.get("finance"):
        fn      = rec["finance"]
        txn_str = " / ".join(
            f"{t['merchant']} {t['amount']:,}원"
            for t in fn["transactions"][:5]
        )
        extra = f" 외 {len(fn['transactions'])-5}건" if len(fn["transactions"]) > 5 else ""
        lines.append(f"💳 소비: 총 {fn['total_spent']:,}원 | {txn_str}{extra}")
    else:
        lines.append("💳 소비: 데이터 없음")

    return "\n".join(lines)


# ── 주별 자연어 요약 ──────────────────────────────────────────────────────────

def format_weekly_summary(week_rec: dict, baseline: dict) -> str:
    """주별 레코드 → LLM 입력용 자연어 요약 텍스트"""
    lines = [f"[{week_rec['week']} | {week_rec['date_range']}]"]

    s = week_rec.get("sleep", {})
    if s.get("avg_hours"):
        sign = "+" if s["vs_baseline"] >= 0 else ""
        lines.append(f"😴 평균 수면: {s['avg_hours']}시간 (평균 대비 {sign}{s['vs_baseline']}h)")

    st = week_rec.get("steps", {})
    if st.get("avg_daily"):
        sign = "+" if st["vs_baseline"] >= 0 else ""
        lines.append(f"🚶 평균 걸음수: {st['avg_daily']:,}보 (평균 대비 {sign}{st['vs_baseline']:,}보)")

    sc = week_rec.get("screentime", {})
    if sc.get("avg_daily_min"):
        sign = "+" if sc["vs_baseline"] >= 0 else ""
        lines.append(f"📱 평균 스크린타임: {sc['avg_daily_min']}분 (평균 대비 {sign}{sc['vs_baseline']}분)")

    fn = week_rec.get("finance", {})
    if fn.get("total_spent_week"):
        lines.append(f"💳 주간 총 지출: {fn['total_spent_week']:,}원")

    w = week_rec.get("weather", {})
    if w.get("avg_temp"):
        lines.append(f"🌤️ 주간 날씨: {w['main_condition']}, 평균 {w['avg_temp']}°C")

    cal = week_rec.get("calendar", {})
    if cal.get("total_events"):
        cats = ", ".join(cal["categories"])
        lines.append(f"📅 주간 일정: 총 {cal['total_events']}개 ({cats})")

    return "\n".join(lines)