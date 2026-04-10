"""
run_llm_analysis_with_score.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
기존 run_llm_analysis.py 와 완전히 동일한 동작에
주간 점수 계산 + 리포트 삽입 + JSON 저장을 추가한 버전입니다.

기존 파일을 건드리지 않으려면 이 파일을 그대로 사용하세요.
기존 파일에 합치려면 주석 "[DIFF]" 부분만 추가하면 됩니다.

실행:
    python run_llm_analysis_with_score.py --week 2025-W47
    python run_llm_analysis_with_score.py --all-weeks
    python run_llm_analysis_with_score.py --week 2025-W47 --score-only  # LLM 없이 점수만
"""

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src.utils.paths import (
    INTERIM_DAILY_JSON,
    PROCESSED_WEEKLY_JSON,
    PROCESSED_BASELINE,
    PROCESSED_WEEKLY_SCORE,
    WEEKLY_REPORTS_DIR,
    DATA_PROCESSED,
    ensure_dirs,
)
from src.model.evidence import build_week_evidence
from src.model.llm_client import (
    check_ollama_running,
    get_available_models,
    analyze_daily,
    analyze_weekly,
    MODEL_NAME,
)
from src.model.build_llm_input_summary import (
    format_daily_summary,
    format_weekly_summary,
)

# [DIFF] scorer import
from src.model.scorer import calculate_scores, to_score_json

# 점수 블록 마커 (리포트 파일 내 삽입 위치 식별용)
_SCORE_START = "## [SCORE_BLOCK_START]"
_SCORE_END   = "## [SCORE_BLOCK_END]"

# 점수 누적 저장 경로
WEEKLY_SCORE_JSON = DATA_PROCESSED / "weekly_score.json"


# ── 데이터 로드 (기존과 동일) ─────────────────────────────────────────────────
def load_processed_data():
    if not INTERIM_DAILY_JSON.exists():
        print("❌ 전처리 데이터가 없습니다. 먼저: python run_weekly_llm_report.py")
        sys.exit(1)

    with open(INTERIM_DAILY_JSON,    encoding="utf-8") as f:
        daily_records  = json.load(f)
    with open(PROCESSED_WEEKLY_JSON, encoding="utf-8") as f:
        weekly_summary = json.load(f)
    with open(PROCESSED_BASELINE,    encoding="utf-8") as f:
        baseline       = json.load(f)

    return daily_records, weekly_summary, baseline


# ── [DIFF] 점수 계산 + 리포트 삽입 + JSON 저장 ────────────────────────────────
def _run_scorer(week_key: str, weekly_summary: dict, daily_records: dict) -> None:
    """
    1. 점수 계산
    2. weekly_reports/weekly_{week}.txt 앞에 점수 블록 삽입 (또는 갱신)
    3. data/processed/weekly_score.json 에 누적 저장
    """
    if week_key not in weekly_summary:
        print(f"  [scorer] ⚠️  {week_key} 요약 데이터 없음, 점수 계산 건너뜀")
        return

    ws_entry = weekly_summary[week_key]

    try:
        result = calculate_scores(week_key, ws_entry, daily_records)
    except Exception as e:
        print(f"  [scorer] ⚠️  점수 계산 오류: {e}")
        return

    print(f"  [scorer] 종합 {result.total:.1f}점 ({result.grade})")
    print(f"  [scorer] {result.summary_line}")

    # ── 리포트 파일에 점수 블록 삽입 ────────────────────────────────────────
    report_path = WEEKLY_REPORTS_DIR / f"weekly_{week_key}.txt"
    wrapped = f"{_SCORE_START}\n{result.score_block}\n{_SCORE_END}\n"

    if report_path.exists():
        original = report_path.read_text(encoding="utf-8")
        if _SCORE_START in original:
            # 기존 블록 교체
            updated = re.sub(
                rf"{re.escape(_SCORE_START)}.*?{re.escape(_SCORE_END)}\n?",
                wrapped,
                original,
                flags=re.DOTALL,
            )
        else:
            # 파일 맨 앞에 삽입
            updated = wrapped + "\n" + original
        report_path.write_text(updated, encoding="utf-8")
    else:
        # 리포트 파일이 아직 없으면 점수만 단독 저장
        report_path.write_text(wrapped, encoding="utf-8")

    print(f"  [scorer] 리포트 업데이트: {report_path.name}")

    # ── weekly_score.json 누적 저장 ─────────────────────────────────────────
    if WEEKLY_SCORE_JSON.exists():
        with open(WEEKLY_SCORE_JSON, encoding="utf-8") as f:
            all_scores = json.load(f)
    else:
        all_scores = {}
    start_str, end_str = ws_entry["date_range"].split(" ~ ")
    score_data = to_score_json(result)
    ordered_score_data = {
        "period": {
            "start": start_str,
            "end": end_str,
        }
    }
    ordered_score_data.update(score_data)
    all_scores[week_key] = ordered_score_data
    WEEKLY_SCORE_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(WEEKLY_SCORE_JSON, "w", encoding="utf-8") as f:
        json.dump(all_scores, f, ensure_ascii=False, indent=2)

    print(f"  [scorer] JSON 저장: {WEEKLY_SCORE_JSON.name}")


# ── 일간 분석 (기존과 동일) ───────────────────────────────────────────────────
def run_daily_analysis(date_str, daily_records, baseline, model):
    if date_str not in daily_records:
        print(f"❌ {date_str} 데이터 없음")
        return

    rec = daily_records[date_str]
    summary_text = format_daily_summary(rec, baseline)

    print(f"\n📋 입력 요약:\n{'─'*50}")
    print(summary_text)
    print(f"{'─'*50}")
    print(f"\n🤖 LLM 분석 중... (모델: {model})")

    result   = analyze_daily(summary_text, model=model)
    out_path = WEEKLY_REPORTS_DIR / f"daily_{date_str}.txt"
    out_path.write_text(
        f"[분석 날짜: {date_str}] [모델: {model}]\n\n"
        f"[입력 요약]\n{summary_text}\n\n"
        f"[LLM 분석 결과]\n{result}",
        encoding="utf-8",
    )
    print(f"\n✅ 결과 저장: {out_path}")


# ── 주간 분석 (기존 + scorer 추가) ───────────────────────────────────────────
def run_weekly_analysis(
    week_key, daily_records, weekly_summary, baseline, model,
    score_only: bool = False,
):
    if week_key not in weekly_summary:
        print(f"❌ {week_key} 데이터 없음. 사용 가능: {list(weekly_summary.keys())}")
        return

    # [DIFF] 점수 계산 먼저 실행 (LLM 없이도 동작)
    print(f"\n📊 점수 계산 중...")
    _run_scorer(week_key, weekly_summary, daily_records)

    if score_only:
        return

    # ── 기존 LLM 분석 (변경 없음) ────────────────────────────────────────────
    wrec        = weekly_summary[week_key]
    weekly_text = format_weekly_summary(wrec, baseline)
    start_str, end_str = wrec["date_range"].split(" ~ ")

    evidence_block = build_week_evidence(daily_records, start_str, end_str)
    enhanced_weekly_text = f"\n{evidence_block}\n\n[WEEKLY SUMMARY]\n{weekly_text}\n"

    daily_texts = [
        format_daily_summary(daily_records[d], baseline)
        for d in sorted(daily_records.keys())
        if start_str <= d <= end_str
    ]

    print(f"\n🤖 LLM 분석 중... (모델: {model})")
    result = analyze_weekly(enhanced_weekly_text, daily_texts, model=model)

    out_path = WEEKLY_REPORTS_DIR / f"weekly_{week_key}.txt"

    # 점수 블록만 유지하고 LLM 결과는 항상 새로 덮어씀
    score_block = ""
    if out_path.exists():
        existing = out_path.read_text(encoding="utf-8")
        if _SCORE_START in existing:
            m = re.search(
                rf"{re.escape(_SCORE_START)}.*?{re.escape(_SCORE_END)}\n?",
                existing, re.DOTALL
            )
            if m:
                score_block = m.group(0) + "\n"

    out_path.write_text(
        score_block +
        f"[분석 주차: {week_key}] [모델: {model}]\n\n"
        f"[주간 요약]\n{weekly_text}\n\n"
        f"[LLM 분석 결과]\n{result}",
        encoding="utf-8",
    )

    # ── JSON 저장 추가 ──────────────────────────────────────────
    json_out_path = out_path.with_suffix(".json")

    # period 날짜 계산
    start_str, end_str = wrec["date_range"].split(" ~ ")

    report_json = {
        "period": {
            "start": start_str,
            "end": end_str,
        },
        "week_id": week_key,
        "model": model,
        "report_text": result,
        "quality_notes": [],
    }
    json_out_path.write_text(
        json.dumps(report_json, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"  ✅ JSON 저장: {json_out_path.name}")

    print(f"\n✅ 결과 저장: {out_path}")


# ── 전체 주 분석 ──────────────────────────────────────────────────────────────
def run_all_weeks(daily_records, weekly_summary, baseline, model, score_only: bool = False):
    weeks = sorted(weekly_summary.keys())
    print(f"\n📅 전체 {len(weeks)}주 분석 시작")

    for i, week_key in enumerate(weeks, 1):
        print(f"\n{'='*60}")
        print(f" [{i}/{len(weeks)}] {week_key} 분석 중...")
        print(f"{'='*60}")
        run_weekly_analysis(week_key, daily_records, weekly_summary, baseline, model, score_only)


# ── 메인 ─────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="LifeLog LLM 분석 + 점수 계산")
    parser.add_argument("--date",       type=str,            help="날짜 분석 (YYYY-MM-DD)")
    parser.add_argument("--week",       type=str,            help="주차 분석 (YYYY-WXX)")
    parser.add_argument("--all-weeks",  action="store_true", help="전체 주 분석")
    parser.add_argument("--score-only", action="store_true", help="LLM 없이 점수만 계산")
    parser.add_argument("--model",      type=str,            default=MODEL_NAME)
    args = parser.parse_args()

    print("=" * 60)
    print(" LifeLog Analysis — LLM 분석 + 주간 점수")
    print("=" * 60)

    # score-only 모드는 Ollama 불필요
    if not args.score_only:
        print("\n🔍 Ollama 서버 확인 중...")
        if not check_ollama_running():
            print("❌ Ollama 서버 미실행. $ ollama serve")
            sys.exit(1)
        available = get_available_models()
        print(f"✅ Ollama 연결 성공 | 설치 모델: {available or '없음'}")
        model = args.model
        if not any(model in m for m in available):
            print(f"⚠️  '{model}' 없음. 설치: ollama pull {model}")
            if available:
                model = available[0]
                print(f"→ '{model}' 사용")
            else:
                sys.exit(1)
    else:
        model = args.model
        print("ℹ️  score-only 모드: LLM 호출 없이 점수만 계산합니다.")

    ensure_dirs()
    daily_records, weekly_summary, baseline = load_processed_data()
    dates = sorted(daily_records.keys())
    print(f"📂 데이터: {len(daily_records)}일 ({dates[0]} ~ {dates[-1]}), {len(weekly_summary)}주")

    if not args.date and not args.week and not args.all_weeks:
        print("\n사용 예시:")
        print(f"  python {Path(__file__).name} --week {sorted(weekly_summary.keys())[0]}")
        print(f"  python {Path(__file__).name} --week 2025-W47 --score-only")
        print(f"  python {Path(__file__).name} --all-weeks --score-only")
        return

    if args.date:
        run_daily_analysis(args.date, daily_records, baseline, model)
    elif args.week:
        run_weekly_analysis(
            args.week, daily_records, weekly_summary, baseline, model,
            score_only=args.score_only,
        )
    elif args.all_weeks:
        run_all_weeks(
            daily_records, weekly_summary, baseline, model,
            score_only=args.score_only,
        )

    print("\n" + "=" * 60)
    print(f" 완료! weekly_reports/ 및 {WEEKLY_SCORE_JSON.name} 확인")
    print("=" * 60)


if __name__ == "__main__":
    main()
