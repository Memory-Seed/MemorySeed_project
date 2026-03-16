"""
preprocessor.py
원본 JSON 데이터 → 일별 / 주별 요약 dict 생성
"""

from datetime import datetime, date, timedelta
from collections import defaultdict
import re
from typing import Optional

from src.constants import KST


class LifeDataPreprocessor:
    def __init__(
        self,
        sleep: list[dict],
        steps: list[dict],
        screentime: list[dict],
        calendar: dict,
        notification: list[dict],
        weather: list[dict],
    ):
        self.sleep        = sleep
        self.steps        = steps
        self.screentime   = screentime
        self.cal_items    = calendar.get("items", [])
        self.notification = notification
        self.weather      = weather

    # ── 공개 메서드 ──────────────────────────

    def daily_summary(self, target: str | date) -> dict:
        if isinstance(target, str):
            target = date.fromisoformat(target)
        return {
            "date":        str(target),
            "sleep":       self._sleep(target),
            "steps":       self._steps(target),
            "screentime":  self._screentime(target),
            "calendar":    self._calendar(target),
            "weather":     self._weather(target),
            "spending":    self._spending(target),
        }

    def weekly_summary(self, start: str | date, end: str | date) -> dict:
        if isinstance(start, str): start = date.fromisoformat(start)
        if isinstance(end,   str): end   = date.fromisoformat(end)

        days, cursor = [], start
        while cursor <= end:
            days.append(self.daily_summary(cursor))
            cursor += timedelta(days=1)

        return {
            "period":      {"start": str(start), "end": str(end)},
            "days_count":  len(days),
            "sleep":       self._weekly_sleep(days),
            "steps":       self._weekly_steps(days),
            "screentime":  self._weekly_screentime(days),
            "calendar":    self._weekly_calendar(days),
            "weather":     self._weekly_weather(days),
            "spending":    self._weekly_spending(days),
            "daily_list":  days,
        }

    # ── 일별 집계 ────────────────────────────

    def _sleep(self, target: date) -> Optional[dict]:
        for s in self.sleep:
            end_dt   = datetime.fromisoformat(s["endTime"].replace("Z", "+00:00")).astimezone(KST)
            start_dt = datetime.fromisoformat(s["startTime"].replace("Z", "+00:00")).astimezone(KST)
            if end_dt.date() == target:
                return {
                    "bedtime":        start_dt.strftime("%H:%M"),
                    "wakeup":         end_dt.strftime("%H:%M"),
                    "bedtime_hour":   start_dt.hour,          # 이상치 탐지용
                    "duration_hours": round((end_dt - start_dt).total_seconds() / 3600, 1),
                }
        return None

    def _steps(self, target: date) -> int:
        total = 0
        for s in self.steps:
            dt = datetime.fromisoformat(s["startTime"].replace("Z", "+00:00")).astimezone(KST)
            if dt.date() == target:
                total += s["count"]
        return total

    # 오락성 앱 패키지 목록 (게임/동영상/웹툰 등)
    ENTERTAINMENT_PACKAGES = {
        "com.pubg.krmobile", "com.supercell.clashroyale",
        "com.google.android.youtube", "com.netflix.mediaclient",
        "com.naver.linewebtoon",
    }

    def _screentime(self, target: date) -> dict:
        by_app: dict[str, int] = defaultdict(int)
        for s in self.screentime:
            dt = datetime.fromtimestamp(s["firstTimeStamp"] / 1000, tz=KST)
            if dt.date() == target:
                by_app[s["packageName"]] += s["totalTimeInForeground"] // 60000

        # 사용시간 기준 정렬
        sorted_apps = sorted(by_app.items(), key=lambda x: -x[1])

        # 상위 3개 앱
        top3 = [
            {"package": pkg, "minutes": mins}
            for pkg, mins in sorted_apps[:3]
        ]

        # 오락성 앱 총 사용시간
        entertainment_min = sum(
            mins for pkg, mins in by_app.items()
            if pkg in self.ENTERTAINMENT_PACKAGES
        )

        return {
            "total_min":        sum(by_app.values()),
            "top3_apps":        top3,
            "entertainment_min": entertainment_min,
            "all_apps":         [
                {"package": pkg, "minutes": mins}
                for pkg, mins in sorted_apps
            ],
        }

    def _calendar(self, target: date) -> list[dict]:
        events = []
        for ev in self.cal_items:
            raw = ev["start"].get("dateTime", ev["start"].get("date", ""))
            if target.isoformat() in raw:
                events.append({
                    "name": ev["summary"],
                    "time": raw[11:16] if "T" in raw else "종일",
                })
        return sorted(events, key=lambda x: x["time"])

    def _weather(self, target: date) -> Optional[dict]:
        records = [
            w for w in self.weather
            if datetime.fromisoformat(w["LocalObservationDateTime"]).astimezone(KST).date() == target
        ]
        if not records:
            return None
        temps       = [w["Temperature"]["Metric"]["Value"] for w in records]
        feel_temps  = [w["RealFeelTemperature"]["Metric"]["Value"] for w in records if w.get("RealFeelTemperature")]
        humidities  = [w["RelativeHumidity"] for w in records if w.get("RelativeHumidity")]
        precip      = max(w.get("PrecipitationProbability", 0) for w in records)
        conditions  = list(dict.fromkeys(w["WeatherText"] for w in records))[:2]

        return {
            "min_temp_c":      round(min(temps), 1),
            "max_temp_c":      round(max(temps), 1),
            "min_feel_temp_c": round(min(feel_temps), 1) if feel_temps else None,
            "max_feel_temp_c": round(max(feel_temps), 1) if feel_temps else None,
            "avg_humidity_pct": round(sum(humidities) / len(humidities)) if humidities else None,
            "max_precip_pct":  precip,
            "conditions":      conditions,
            "rain_expected":   precip >= 40,  # 40% 이상이면 우산 챙기기
        }

    def _spending(self, target: date) -> dict:
        total = 0
        transactions = []
        for n in self.notification:
            big  = n.get("extras", {}).get("android.bigText", "") or ""
            text = n.get("extras", {}).get("android.text",    "") or ""
            full = big + " " + text
            if "출금" not in full:
                continue
            dt = datetime.fromtimestamp(n["postTime"] / 1000, tz=KST)
            if dt.date() != target:
                continue
            amount_match = re.search(r"출금\s*([\d,]+)", full)
            if not amount_match:
                continue
            amount = int(amount_match.group(1).replace(",", ""))
            name_match = re.search(r"\*{3}\d+\s+(.+?)\s+FBS", big)
            name = name_match.group(1) if name_match else "기타"
            total += amount
            transactions.append({"name": name, "amount": amount})
        transactions.sort(key=lambda x: -x["amount"])
        return {
            "total_spent":   total,
            "transactions":  transactions,
            "top_merchants": [t["name"] for t in transactions[:3]],
        }

    # ── 주별 집계 ────────────────────────────

    def _weekly_sleep(self, days: list[dict]) -> dict:
        sleeps = [d["sleep"] for d in days if d["sleep"]]
        if not sleeps:
            return {}
        durs = [s["duration_hours"] for s in sleeps]

        def time_to_mins(t: str) -> int:
            h, m = int(t[:2]), int(t[3:])
            total = h * 60 + m
            # 취침 시각: 오후 9시(21:00) 이전이면 다음날로 간주 (+24h)
            # 예: 23:22 → 1402분, 00:49 → 49 + 1440 = 1489분으로 연속 처리
            return total

        def avg_bedtime(times: list[str]) -> str:
            # 자정 넘기는 취침 시각 보정: 22시 미만이면 +1440분 (다음날 새벽)
            adj = []
            for t in times:
                m = time_to_mins(t)
                if m < 22 * 60:   # 22시 이전 = 새벽 (자정 넘긴 것)
                    m += 1440
                adj.append(m)
            avg = sum(adj) // len(adj)
            avg = avg % 1440  # 24시간 범위로 환원
            return f"{avg // 60:02d}:{avg % 60:02d}"

        def avg_wakeup(times: list[str]) -> str:
            mins_list = [time_to_mins(t) for t in times]
            avg = sum(mins_list) // len(mins_list)
            return f"{avg // 60:02d}:{avg % 60:02d}"

        return {
            "avg_duration_hours": round(sum(durs) / len(durs), 1),
            "min_duration_hours": min(durs),
            "max_duration_hours": max(durs),
            "avg_bedtime":  avg_bedtime([s["bedtime"] for s in sleeps]),
            "avg_wakeup":   avg_wakeup([s["wakeup"]  for s in sleeps]),
            "days_recorded": len(sleeps),
        }

    def _weekly_steps(self, days: list[dict]) -> dict:
        counts = [d["steps"] for d in days]
        return {
            "total":           sum(counts),
            "daily_avg":       round(sum(counts) / len(counts)),
            "max_day":         max(counts),
            "days_over_10000": sum(1 for c in counts if c >= 10000),
        }

    def _weekly_screentime(self, days: list[dict]) -> dict:
        app_totals: dict[str, int] = defaultdict(int)
        totals = []
        for d in days:
            totals.append(d["screentime"]["total_min"])
            for app in d["screentime"].get("all_apps", d["screentime"].get("apps", [])):
                app_totals[app["package"]] += app["minutes"]

        top_apps = [
            {"package": pkg, "minutes": mins}
            for pkg, mins in sorted(app_totals.items(), key=lambda x: -x[1])[:10]
        ]

        return {
            "daily_avg_min": round(sum(totals) / len(totals)),
            "total_min":     sum(totals),
            "top_apps":      top_apps,   # 주간 상위 앱, LLM이 분류
        }

    def _weekly_calendar(self, days: list[dict]) -> dict:
        all_events = [ev for d in days for ev in d["calendar"]]
        kw_counts: dict[str, int] = defaultdict(int)
        for ev in all_events:
            for kw in ["수업", "운동", "약속", "러닝", "스터디", "회의", "알바"]:
                if kw in ev["name"]:
                    kw_counts[kw] += 1
        return {
            "total_events":   len(all_events),
            "keyword_counts": dict(kw_counts),
        }

    def _weekly_weather(self, days: list[dict]) -> dict:
        records = [d["weather"] for d in days if d["weather"]]
        if not records:
            return {}
        return {
            "avg_max_temp_c": round(sum(r["max_temp_c"] for r in records) / len(records), 1),
            "avg_min_temp_c": round(sum(r["min_temp_c"] for r in records) / len(records), 1),
            "avg_precip_pct": round(sum(r["max_precip_pct"] for r in records) / len(records)),
        }

    def _weekly_spending(self, days: list[dict]) -> dict:
        total = 0
        merchant_counts: dict[str, int] = defaultdict(int)
        for d in days:
            sp = d.get("spending", {})
            total += sp.get("total_spent", 0)
            for m in sp.get("top_merchants", []):
                merchant_counts[m] += 1
        top = sorted(merchant_counts.items(), key=lambda x: -x[1])[:3]
        return {
            "total_spent":    total,
            "top_merchants":  [m for m, _ in top],
            "daily_avg_spent": round(total / len(days)) if days else 0,
        }
