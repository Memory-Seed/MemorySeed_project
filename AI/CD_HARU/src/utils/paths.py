"""
paths.py — 프로젝트 경로 중앙 관리
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

DATA_RAW       = ROOT / "data" / "raw"
DATA_INTERIM   = ROOT / "data" / "interim"
DATA_PROCESSED = ROOT / "data" / "processed"

RAW_FILES = {
    "sleep":        DATA_RAW / "sleep.csv",
    "steps":        DATA_RAW / "steps.csv",
    "screentime":   DATA_RAW / "screentime.csv",
    "weather":      DATA_RAW / "accuweather.csv",
    "calendar":     DATA_RAW / "google_calendar.csv",
    "notification": DATA_RAW / "notification.json",
}

INTERIM_DAILY_JSON     = DATA_INTERIM   / "daily_records.json"
PROCESSED_WEEKLY_JSON  = DATA_PROCESSED / "weekly_summary.json"
PROCESSED_BASELINE     = DATA_PROCESSED / "baseline.json"
PROCESSED_WEEKLY_SCORE = DATA_PROCESSED / "weekly_score.json"

SUMMARIES_DIR      = ROOT / "summaries"
WEEKLY_REPORTS_DIR = ROOT / "weekly_reports"


def ensure_dirs():
    for d in [DATA_RAW, DATA_INTERIM, DATA_PROCESSED, SUMMARIES_DIR, WEEKLY_REPORTS_DIR]:
        d.mkdir(parents=True, exist_ok=True)
