"""
parsers.py — 도메인별 Raw 데이터 파서
각 함수는 CSV/JSON 파일을 읽어 { 'YYYY-MM-DD': {...} } 형태의 dict를 반환합니다.
"""

import csv
import json
import re
from collections import defaultdict
from datetime import datetime

from src.utils.constants import APP_MAP, WEATHER_CONDITION_KR
from src.utils.helpers import (
    utc_str_to_kst, ms_to_kst,
    assign_sleep_date,
    classify_calendar_event, classify_merchant,
)


# ── 1. 수면 ───────────────────────────────────────────────────────────────────

def parse_sleep(filepath) -> dict:
    """
    sleep.csv → 날짜별 수면 기록
    반환: { 'YYYY-MM-DD': { bedtime, wakeup, duration_hours, note } }
    """
    result = {}

    with open(filepath, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            bedtime  = utc_str_to_kst(row["startTime"])
            wakeup   = utc_str_to_kst(row["endTime"])
            duration = (wakeup - bedtime).total_seconds() / 3600
            date_key = assign_sleep_date(bedtime)

            if date_key in result:
                # 같은 날 여러 기록 → 합산 처리
                result[date_key]["duration_hours"] += round(duration, 1)
                result[date_key]["note"] = "분할 수면"
            else:
                result[date_key] = {
                    "bedtime":        bedtime.strftime("%H:%M"),
                    "wakeup":         wakeup.strftime("%H:%M"),
                    "duration_hours": round(duration, 1),
                    "note":           "",
                }

    return result


# ── 2. 걸음수 ─────────────────────────────────────────────────────────────────

def parse_steps(filepath) -> dict:
    """
    steps.csv → 날짜별 걸음수 합산
    반환: { 'YYYY-MM-DD': { total_steps, active_segments } }
    """
    daily = defaultdict(lambda: {"total_steps": 0, "active_segments": 0})

    with open(filepath, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            date_key = utc_str_to_kst(row["startTime"]).strftime("%Y-%m-%d")
            daily[date_key]["total_steps"]     += int(row["count"])
            daily[date_key]["active_segments"] += 1

    return dict(daily)


# ── 3. 스크린타임 ─────────────────────────────────────────────────────────────

def parse_screentime(filepath) -> dict:
    """
    screentime.csv → 날짜별 앱 사용시간 집계 (ms → 분 변환)
    반환: { 'YYYY-MM-DD': { total_min, by_category, top_apps } }
    """
    daily = defaultdict(lambda: {
        "total_min":   0.0,
        "by_category": defaultdict(float),
        "by_app":      defaultdict(float),
    })

    with open(filepath, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            date_key = ms_to_kst(int(row["firstTimeStamp"])).strftime("%Y-%m-%d")
            pkg      = row["packageName"]
            minutes  = int(row["totalTimeInForeground"]) / 1000 / 60

            app_name, category = APP_MAP.get(pkg, (pkg.split(".")[-1], "기타"))

            daily[date_key]["total_min"]                += minutes
            daily[date_key]["by_category"][category]    += minutes
            daily[date_key]["by_app"][app_name]         += minutes

    # 정리
    result = {}
    for date_key, data in daily.items():
        top_apps = sorted(data["by_app"].items(), key=lambda x: -x[1])[:3]
        result[date_key] = {
            "total_min":   round(data["total_min"], 1),
            "by_category": {k: round(v, 1) for k, v in data["by_category"].items()},
            "top_apps":    [{"app": a, "min": round(m, 1)} for a, m in top_apps],
        }

    return result


# ── 4. 날씨 ───────────────────────────────────────────────────────────────────

def parse_weather(filepath) -> dict:
    """
    accuweather.csv → 날짜별 날씨 집계 (시간당 → 일별 평균)
    반환: { 'YYYY-MM-DD': { avg_temp, min_temp, max_temp, avg_feel_temp,
                             condition, precip_prob, avg_humidity } }
    """
    daily = defaultdict(list)

    with open(filepath, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            dt       = datetime.fromisoformat(row["LocalObservationDateTime"])
            date_key = dt.strftime("%Y-%m-%d")
            daily[date_key].append({
                "temp":      float(row["TemperatureValue"]),
                "feel_temp": float(row["RealFeelTemperatureValue"]),
                "precip":    int(row["PrecipitationProbability"]),
                "humidity":  int(row["RelativeHumidity"]),
                "condition": row["WeatherText"],
            })

    result = {}
    for date_key, records in daily.items():
        temps      = [r["temp"]      for r in records]
        feel_temps = [r["feel_temp"] for r in records]
        humidities = [r["humidity"]  for r in records]
        precips    = [r["precip"]    for r in records]
        conditions = [r["condition"] for r in records]
        main_cond  = max(set(conditions), key=conditions.count)

        result[date_key] = {
            "avg_temp":      round(sum(temps) / len(temps), 1),
            "min_temp":      round(min(temps), 1),
            "max_temp":      round(max(temps), 1),
            "avg_feel_temp": round(sum(feel_temps) / len(feel_temps), 1),
            "condition":     WEATHER_CONDITION_KR.get(main_cond, main_cond),
            "precip_prob":   max(precips),
            "avg_humidity":  round(sum(humidities) / len(humidities), 1),
        }

    return result


# ── 5. 캘린더 ─────────────────────────────────────────────────────────────────

def parse_calendar(filepath) -> dict:
    """
    google_calendar.csv → 날짜별 이벤트 목록
    반환: { 'YYYY-MM-DD': [ { summary, category, start, end, duration_min } ] }
    """
    daily = defaultdict(list)

    with open(filepath, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            start    = datetime.fromisoformat(row["startDateTime"])
            end      = datetime.fromisoformat(row["endDateTime"])
            date_key = start.strftime("%Y-%m-%d")
            duration = int((end - start).total_seconds() / 60)

            daily[date_key].append({
                "summary":      row["summary"],
                "category":     classify_calendar_event(row["summary"]),
                "start":        start.strftime("%H:%M"),
                "end":          end.strftime("%H:%M"),
                "duration_min": duration,
            })

    # 시작 시각 기준 정렬
    return {k: sorted(v, key=lambda x: x["start"]) for k, v in daily.items()}


# ── 6. 알림 (금융) ───────────────────────────────────────────────────────────

def parse_notification(filepath) -> dict:
    """
    notification.json → KB은행 알림에서 거래 내역 파싱 → 날짜별 소비 집계
    반환: { 'YYYY-MM-DD': { total_spent, total_received, balance_end,
                             transactions: [...] } }
    """
    PATTERN = re.compile(
        r"(입금|출금)\s+([\d,]+)원\n.+?\s(\S+)\s+FBS(?:입금|출금)\s+[\d,]+\s+잔액([\d,]+)"
    )

    daily = defaultdict(lambda: {
        "total_spent":    0,
        "total_received": 0,
        "balance_end":    0,
        "transactions":   [],
    })

    with open(filepath, encoding="utf-8") as f:
        data = json.load(f)

    for item in data:
        ts       = ms_to_kst(item["postTime"])
        date_key = ts.strftime("%Y-%m-%d")
        big_text = item["extras"].get("android.bigText", "")

        if not big_text:
            continue

        m = PATTERN.search(big_text)
        if not m:
            continue

        txn_type = m.group(1)
        amount   = int(m.group(2).replace(",", ""))
        merchant = m.group(3)
        balance  = int(m.group(4).replace(",", ""))

        daily[date_key]["balance_end"] = balance
        daily[date_key]["transactions"].append({
            "time":     ts.strftime("%H:%M"),
            "type":     txn_type,
            "merchant": merchant,
            "amount":   amount,
            "category": classify_merchant(merchant) if txn_type == "출금" else "수입",
        })

        if txn_type == "출금":
            daily[date_key]["total_spent"]    += amount
        else:
            daily[date_key]["total_received"] += amount

    return dict(daily)