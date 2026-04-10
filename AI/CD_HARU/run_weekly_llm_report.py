"""
run_weekly_llm_report.py — LifeLog 전처리 파이프라인 메인 실행 파일

실행 방법:
    프로젝트 루트(CD_HARU/)에서:
    $ python run_weekly_llm_report.py

출력:
    data/interim/daily_records.json   — 일별 통합 레코드
    data/processed/weekly_summary.json — 주별 요약
    data/processed/baseline.json       — 개인 베이스라인
    summaries/daily/YYYY-MM-DD.txt    — 일별 자연어 요약
    summaries/weekly/YYYY-WXX.txt     — 주별 자연어 요약
"""

import json
import sys
from pathlib import Path

# ── 경로 설정: 프로젝트 루트를 sys.path에 추가 ────────────────────────────────
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src.utils.paths import (
    RAW_FILES,
    INTERIM_DAILY_JSON, PROCESSED_WEEKLY_JSON, PROCESSED_BASELINE,
    SUMMARIES_DIR, WEEKLY_REPORTS_DIR,
    ensure_dirs,
)
from src.model.parsers import (
    parse_sleep, parse_steps, parse_screentime,
    parse_weather, parse_calendar, parse_notification,
)
from src.model.build_llm_input_summary import (
    compute_baseline,
    build_daily_records,
    build_weekly_summary,
    format_daily_summary,
    format_weekly_summary,
)


def main():
    print("=" * 60)
    print("  LifeLog Analysist — 전처리 파이프라인")
    print("=" * 60)

    # 디렉토리 보장
    ensure_dirs()
    (SUMMARIES_DIR / "daily").mkdir(exist_ok=True)
    (SUMMARIES_DIR / "weekly").mkdir(exist_ok=True)

    # ── Step 1: 도메인별 파싱 ─────────────────────────────────────────────────
    print("\n[Step 1] Raw 데이터 파싱 중...")

    sleep_data    = parse_sleep(RAW_FILES["sleep"])
    steps_data    = parse_steps(RAW_FILES["steps"])
    screen_data   = parse_screentime(RAW_FILES["screentime"])
    weather_data  = parse_weather(RAW_FILES["weather"])
    calendar_data = parse_calendar(RAW_FILES["calendar"])
    notif_data    = parse_notification(RAW_FILES["notification"])

    print(f"  ✅ 수면:       {len(sleep_data)}일")
    print(f"  ✅ 걸음수:     {len(steps_data)}일")
    print(f"  ✅ 스크린타임:  {len(screen_data)}일")
    print(f"  ✅ 날씨:       {len(weather_data)}일")
    print(f"  ✅ 캘린더:     {len(calendar_data)}일 (이벤트 있는 날)")
    print(f"  ✅ 금융 알림:   {len(notif_data)}일")

    # ── Step 2: 일별 통합 ─────────────────────────────────────────────────────
    print("\n[Step 2] 일별 데이터 통합 중...")
    daily_records = build_daily_records(
        sleep_data, steps_data, screen_data,
        weather_data, calendar_data, notif_data,
    )
    print(f"  ✅ 총 {len(daily_records)}일 레코드 생성")

    # ── Step 3: 베이스라인 계산 ───────────────────────────────────────────────
    print("\n[Step 3] 개인 베이스라인 계산 중...")
    baseline = compute_baseline(daily_records)
    print(f"  ✅ 평균 수면:       {baseline['avg_sleep_hours']}시간")
    print(f"  ✅ 평균 걸음수:     {baseline['avg_steps']:,}보")
    print(f"  ✅ 평균 스크린타임:  {baseline['avg_screentime_min']}분")

    # ── Step 4: 주별 요약 ─────────────────────────────────────────────────────
    print("\n[Step 4] 주별 요약 생성 중...")
    weekly_summary = build_weekly_summary(daily_records, baseline)
    print(f"  ✅ 총 {len(weekly_summary)}주 요약 생성")

    # ── Step 5: 자연어 요약 파일 저장 ─────────────────────────────────────────
    print("\n[Step 5] 자연어 요약 파일 저장 중...")

    for date_str, rec in daily_records.items():
        summary_text = format_daily_summary(rec, baseline)
        out_path = SUMMARIES_DIR / "daily" / f"{date_str}.json"
        out_path.write_text(
            json.dumps({"date": date_str, "summary": summary_text}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    for week_key, wrec in weekly_summary.items():
        summary_text = format_weekly_summary(wrec, baseline)
        out_path = SUMMARIES_DIR / "weekly" / f"{week_key}.json"
        out_path.write_text(
            json.dumps({"week_id": week_key, "summary": summary_text}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    print(f"  ✅ 일별 요약: {len(daily_records)}개 파일 → summaries/daily/")
    print(f"  ✅ 주별 요약: {len(weekly_summary)}개 파일 → summaries/weekly/")

    # ── Step 6: JSON 저장 ─────────────────────────────────────────────────────
    print("\n[Step 6] JSON 결과 저장 중...")

    INTERIM_DAILY_JSON.write_text(
        json.dumps(daily_records, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    PROCESSED_WEEKLY_JSON.write_text(
        json.dumps(weekly_summary, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    PROCESSED_BASELINE.write_text(
        json.dumps(baseline, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"  ✅ {INTERIM_DAILY_JSON}")
    print(f"  ✅ {PROCESSED_WEEKLY_JSON}")
    print(f"  ✅ {PROCESSED_BASELINE}")

    # ── 샘플 출력 ─────────────────────────────────────────────────────────────
    print("\n" + "─" * 60)
    print("📋 샘플 — 첫 3일 자연어 요약")
    print("─" * 60)
    for date_str in sorted(daily_records.keys())[:3]:
        print(format_daily_summary(daily_records[date_str], baseline))
        print()

    print("=" * 60)
    print("  전처리 완료!")
    print("=" * 60)


if __name__ == "__main__":
    main()