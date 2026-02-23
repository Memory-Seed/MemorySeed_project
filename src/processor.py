# processor.py
from __future__ import annotations

import json
import re
from typing import Dict, Any, List, Optional, Union

import pandas as pd


# -------------------------
# Time helpers
# -------------------------
def _to_kst(dt_like) -> pd.Timestamp:
    """
    다양한 datetime 입력을 KST(Asia/Seoul) tz-aware Timestamp로 변환.
    - "2024-11-27T07:20:48.310+09:00" 같은 형태
    - "2024-11-26T00:00:00.000Z" 같은 형태
    - "2024-11-27" 같은 date-only 형태
    """
    ts = pd.to_datetime(dt_like, utc=True, errors="coerce")
    if pd.isna(ts):
        ts = pd.to_datetime(dt_like, errors="coerce")
        if pd.isna(ts):
            raise ValueError(f"Cannot parse datetime: {dt_like}")
        if ts.tzinfo is None:
            ts = ts.tz_localize("Asia/Seoul")
        return ts.tz_convert("Asia/Seoul")
    return ts.tz_convert("Asia/Seoul")


def _fmt_hhmm(ts: pd.Timestamp) -> str:
    ts = ts.tz_convert("Asia/Seoul")
    return f"{ts.hour:02d}:{ts.minute:02d}"


def _safe_int(x, default=0) -> int:
    try:
        return int(x)
    except Exception:
        return default


# -------------------------
# Processor
# -------------------------
class DataProcessor:
    """
    JSON 데이터로 일일/주간 요약을 생성.

    - steps.json: [{count, startTime, endTime, ...}, ...]
    - sleep.json: [{startTime, endTime, ...}, ...]
    - screentime.json: [{packageName, firstTimeStamp(ms), totalTimeInForeground(ms), ...}, ...]
    - notification.json: NDJSON (line-delimited JSON)
        - postTime(ms epoch) 우선 사용, isoTime 있으면 fallback
        - extras.android.text / extras.android.bigText에서 "출금 N원"만 지출로 카운트
    - google_calendar.json: {"items":[...]} 기반 일정 요약
    - accuweather.json:
        - 보통 리스트 형태: [{LocalObservationDateTime, Temperature:{Metric:{Value}}, PrecipitationProbability}, ...]
        - 또는 {"hourlyTemperature":[{dateTime, temperature, precipitationProbability, weatherIcon}, ...]}도 호환
    """

    def __init__(
        self,
        steps_path: str = "data/steps.json",
        sleep_path: str = "data/sleep.json",
        billing_path: str = "data/notification.json",
        screen_path: str = "data/screentime.json",
        calendar_path: Optional[str] = None,
        weather_path: Optional[str] = None,
    ):
        self.steps_df = pd.read_json(steps_path)
        self.sleep_df = pd.read_json(sleep_path)
        self.screen_df = pd.read_json(screen_path)
        self.billing_df = self._read_ndjson(billing_path)

        self.calendar: Optional[dict] = None
        self.weather: Optional[Union[dict, list]] = None

        if calendar_path:
            with open(calendar_path, "r", encoding="utf-8") as f:
                self.calendar = json.load(f)
        if weather_path:
            with open(weather_path, "r", encoding="utf-8") as f:
                self.weather = json.load(f)

        self._prep()

    # -------------------------
    # Loading / prep
    # -------------------------
    def _read_ndjson(self, path: str) -> pd.DataFrame:
        """
        NDJSON을 줄 단위로 읽는다.
        깨진 줄(중간 잘림/비정상)은 스킵.
        """
        rows = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                # 혹시 줄 앞에 쓰레기 문자가 붙어도 첫 '{'부터 자르기
                idx = line.find("{")
                if idx == -1:
                    continue
                line = line[idx:]

                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
                except Exception:
                    continue

        return pd.json_normalize(rows) if rows else pd.DataFrame()

    def _prep(self) -> None:
        # steps
        if not self.steps_df.empty:
            self.steps_df["start_kst"] = self.steps_df["startTime"].apply(_to_kst)
            self.steps_df["date"] = self.steps_df["start_kst"].dt.strftime("%Y-%m-%d")

        # sleep
        if not self.sleep_df.empty:
            self.sleep_df["start_kst"] = self.sleep_df["startTime"].apply(_to_kst)
            self.sleep_df["end_kst"] = self.sleep_df["endTime"].apply(_to_kst)
            self.sleep_df["duration_min"] = (
                (self.sleep_df["end_kst"] - self.sleep_df["start_kst"]).dt.total_seconds() / 60.0
            )
            # 기상(종료) 날짜 기준
            self.sleep_df["date"] = self.sleep_df["end_kst"].dt.strftime("%Y-%m-%d")
            self.sleep_df["sleep_start_hour"] = self.sleep_df["start_kst"].dt.hour

        # screen
        if not self.screen_df.empty:
            self.screen_df["start_kst"] = pd.to_datetime(
                self.screen_df["firstTimeStamp"], unit="ms", utc=True, errors="coerce"
            ).dt.tz_convert("Asia/Seoul")
            self.screen_df["date"] = self.screen_df["start_kst"].dt.strftime("%Y-%m-%d")
            self.screen_df["total_min"] = self.screen_df["totalTimeInForeground"] / (1000.0 * 60.0)

        # billing (notification NDJSON)
        if not self.billing_df.empty:
            # 시간: postTime(ms) 우선, isoTime fallback
            if "postTime" in self.billing_df.columns:
                self.billing_df["time_kst"] = (
                    pd.to_datetime(self.billing_df["postTime"], unit="ms", utc=True, errors="coerce")
                    .dt.tz_convert("Asia/Seoul")
                )
            elif "isoTime" in self.billing_df.columns:
                time_kst = pd.to_datetime(self.billing_df["isoTime"], errors="coerce")
                if time_kst.dt.tz is None:
                    time_kst = time_kst.dt.tz_localize("Asia/Seoul")
                else:
                    time_kst = time_kst.dt.tz_convert("Asia/Seoul")
                self.billing_df["time_kst"] = time_kst
            else:
                # 둘 다 없으면 지출 계산 불가
                self.billing_df["time_kst"] = pd.NaT

            self.billing_df = self.billing_df.dropna(subset=["time_kst"])
            if self.billing_df.empty:
                return

            self.billing_df["date"] = self.billing_df["time_kst"].dt.strftime("%Y-%m-%d")

            # 텍스트: text 우선, 없으면 bigText
            text_series = self.billing_df.get("extras.android.text")
            big_series = self.billing_df.get("extras.android.bigText")
            if text_series is None:
                text_series = pd.Series([""] * len(self.billing_df))
            if big_series is None:
                big_series = pd.Series([""] * len(self.billing_df))

            money_re = re.compile(r"(출금|입금)\s*([0-9][0-9,]*)\s*원")

            def parse_spend(text: Any, big: Any) -> int:
                t = ""
                if isinstance(text, str):
                    t += text
                if isinstance(big, str) and big.strip():
                    t += "\n" + big
                if not t:
                    return 0

                m = money_re.search(t)
                if not m:
                    return 0
                kind = m.group(1)
                amt = int(m.group(2).replace(",", ""))

                return amt if kind == "출금" else 0

            self.billing_df["amount_krw"] = [
                parse_spend(t, b) for t, b in zip(text_series.tolist(), big_series.tolist())
            ]

    # -------------------------
    # Calendar helpers
    # -------------------------
    def _iter_calendar_events(self) -> List[Dict[str, Any]]:
        """
        calendar.items를 표준화해 반환:
        [{"date":"YYYY-MM-DD","start_ts":..., "end_ts":..., "title":..., "location":...}, ...]
        """
        if not self.calendar or "items" not in self.calendar:
            return []

        out = []
        for it in self.calendar.get("items", []):
            start = (it.get("start") or {}).get("dateTime") or (it.get("start") or {}).get("date")
            end = (it.get("end") or {}).get("dateTime") or (it.get("end") or {}).get("date")
            if not start or not end:
                continue

            # date-only 이벤트는 00:00로 해석
            if "T" not in start:
                start_ts = pd.to_datetime(start).tz_localize("Asia/Seoul")
            else:
                s = pd.to_datetime(start)
                start_ts = s.tz_convert("Asia/Seoul") if s.tzinfo else s.tz_localize("Asia/Seoul")

            if "T" not in end:
                end_ts = pd.to_datetime(end).tz_localize("Asia/Seoul")
            else:
                e = pd.to_datetime(end)
                end_ts = e.tz_convert("Asia/Seoul") if e.tzinfo else e.tz_localize("Asia/Seoul")

            date = start_ts.strftime("%Y-%m-%d")
            out.append(
                {
                    "date": date,
                    "start_ts": start_ts,
                    "end_ts": end_ts,
                    "title": it.get("summary", "일정"),
                    "location": it.get("location", "") or "",
                }
            )

        out.sort(key=lambda x: x["start_ts"])
        return out

    def _events_in_range(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        events = self._iter_calendar_events()
        if not events:
            return []
        return [e for e in events if start_date <= e["date"] <= end_date]

    def _get_daily_events(self, target_date: str) -> List[Dict[str, Any]]:
        ev = self._events_in_range(target_date, target_date)
        return [
            {
                "title": e["title"],
                "start": _fmt_hhmm(e["start_ts"]),
                "end": _fmt_hhmm(e["end_ts"]),
                "location": e["location"],
            }
            for e in ev
        ]

    def _calendar_daily_brief(self, target_date: str) -> str:
        events = self._get_daily_events(target_date)
        if not events:
            return "오늘 일정 없음"
        top = events[:3]
        return "; ".join(
            [
                f"{e['start']}-{e['end']} {e['title']}{('('+e['location']+')') if e['location'] else ''}"
                for e in top
            ]
        )

    def _calendar_weekly_summary(self, start_date: str, end_date: str) -> Dict[str, Any]:
        events = self._events_in_range(start_date, end_date)
        if not events:
            return {
                "has_calendar": False,
                "event_count": 0,
                "busiest_day": None,
                "busiest_day_count": 0,
                "weekly_events_brief": "이번 주 일정 없음",
            }

        by_day: Dict[str, int] = {}
        for e in events:
            by_day[e["date"]] = by_day.get(e["date"], 0) + 1

        busiest_day = max(by_day.items(), key=lambda x: x[1])[0]
        busiest_day_count = by_day[busiest_day]

        brief_list = []
        for e in events[:5]:
            brief_list.append(
                f"{e['date']} {_fmt_hhmm(e['start_ts'])}-{_fmt_hhmm(e['end_ts'])} {e['title']}"
            )
        weekly_brief = " / ".join(brief_list)

        return {
            "has_calendar": True,
            "event_count": len(events),
            "busiest_day": busiest_day,
            "busiest_day_count": busiest_day_count,
            "weekly_events_brief": weekly_brief,
        }

    # -------------------------
    # Weather helpers
    # -------------------------
    def _weather_rows_for_date(self, target_date: str) -> List[Dict[str, Any]]:
        """
        accuweather 포맷 2가지 모두 지원:
        A) list[{LocalObservationDateTime, Temperature:{Metric:{Value}}, PrecipitationProbability,...}]
        B) dict{"hourlyTemperature":[{dateTime, temperature, precipitationProbability, weatherIcon}, ...]}
        """
        if not self.weather:
            return []

        rows: List[Dict[str, Any]] = []

        # A) 리스트 포맷
        if isinstance(self.weather, list):
            for h in self.weather:
                dt = h.get("LocalObservationDateTime")
                if not dt:
                    continue
                ts = pd.to_datetime(dt, errors="coerce")
                if pd.isna(ts):
                    continue
                ts = ts.tz_localize("Asia/Seoul") if ts.tzinfo is None else ts.tz_convert("Asia/Seoul")

                if ts.strftime("%Y-%m-%d") != target_date:
                    continue

                temp = None
                try:
                    temp = float(((h.get("Temperature") or {}).get("Metric") or {}).get("Value"))
                except Exception:
                    temp = None

                precip = _safe_int(h.get("PrecipitationProbability"), 0)

                rows.append(
                    {
                        "ts": ts,
                        "temp": temp,
                        "icon": None,  # 이 포맷에선 아이콘이 없을 수 있음
                        "precip": precip,
                    }
                )
            return rows

        # B) hourlyTemperature 키 포맷(호환)
        if isinstance(self.weather, dict) and "hourlyTemperature" in self.weather:
            for h in self.weather.get("hourlyTemperature", []):
                dt = h.get("dateTime")
                if not dt:
                    continue
                ts = pd.to_datetime(dt, errors="coerce")
                if pd.isna(ts):
                    continue
                ts = ts.tz_localize("Asia/Seoul") if ts.tzinfo is None else ts.tz_convert("Asia/Seoul")

                if ts.strftime("%Y-%m-%d") != target_date:
                    continue

                rows.append(
                    {
                        "ts": ts,
                        "temp": h.get("temperature"),
                        "icon": h.get("weatherIcon"),
                        "precip": h.get("precipitationProbability"),
                    }
                )
            return rows

        return []

    def _get_daily_weather_summary(self, target_date: str) -> Dict[str, Any]:
        rows = self._weather_rows_for_date(target_date)
        if not rows:
            return {"has_weather": False}

        df = pd.DataFrame(rows)
        if df.empty or "temp" not in df:
            return {"has_weather": False}

        df = df.dropna(subset=["temp"])
        if df.empty:
            return {"has_weather": False}

        tmin = float(df["temp"].min())
        tmax = float(df["temp"].max())
        pmax = int(df["precip"].max()) if "precip" in df else 0

        icon = None
        if "icon" in df and df["icon"].notna().any():
            try:
                icon = int(df["icon"].mode().iloc[0])
            except Exception:
                icon = None

        return {
            "has_weather": True,
            "temp_min": tmin,
            "temp_max": tmax,
            "precip_max": pmax,
            "weather_icon": icon,
        }

    def _weather_daily_brief(self, target_date: str) -> str:
        w = self._get_daily_weather_summary(target_date)
        if not w.get("has_weather"):
            return "오늘 날씨 데이터 없음"
        return f"최저 {w['temp_min']}° / 최고 {w['temp_max']}°, 강수확률 최대 {w['precip_max']}%"

    def _get_weekly_weather_summary(self, start_date: str, end_date: str) -> Dict[str, Any]:
        if not self.weather:
            return {
                "has_weather": False,
                "week_temp_min": None,
                "week_temp_max": None,
                "week_precip_max": 0,
                "week_weather_icon": None,
                "weekly_weather_brief": "이번 주 날씨 데이터 없음",
                "daily_weather": [],
            }

        dates = pd.date_range(start=start_date, end=end_date, freq="D").strftime("%Y-%m-%d").tolist()

        all_rows = []
        daily_list = []
        for d in dates:
            rows = self._weather_rows_for_date(d)
            if not rows:
                continue
            df = pd.DataFrame(rows).dropna(subset=["temp"])
            if df.empty:
                continue

            tmin = float(df["temp"].min())
            tmax = float(df["temp"].max())
            pmax = int(df["precip"].max()) if "precip" in df else 0

            icon = None
            if "icon" in df and df["icon"].notna().any():
                try:
                    icon = int(df["icon"].mode().iloc[0])
                except Exception:
                    icon = None

            daily_list.append(
                {
                    "date": d,
                    "temp_min": tmin,
                    "temp_max": tmax,
                    "precip_max": pmax,
                    "weather_icon": icon,
                }
            )
            all_rows.extend(rows)

        if not all_rows:
            return {
                "has_weather": False,
                "week_temp_min": None,
                "week_temp_max": None,
                "week_precip_max": 0,
                "week_weather_icon": None,
                "weekly_weather_brief": "이번 주 날씨 데이터 없음",
                "daily_weather": [],
            }

        df_all = pd.DataFrame(all_rows).dropna(subset=["temp"])
        if df_all.empty:
            return {
                "has_weather": False,
                "week_temp_min": None,
                "week_temp_max": None,
                "week_precip_max": 0,
                "week_weather_icon": None,
                "weekly_weather_brief": "이번 주 날씨 데이터 없음",
                "daily_weather": [],
            }

        week_temp_min = float(df_all["temp"].min())
        week_temp_max = float(df_all["temp"].max())
        week_precip_max = int(df_all["precip"].max()) if "precip" in df_all else 0

        week_icon = None
        if "icon" in df_all and df_all["icon"].notna().any():
            try:
                week_icon = int(df_all["icon"].mode().iloc[0])
            except Exception:
                week_icon = None

        daily_list_sorted = sorted(daily_list, key=lambda x: x["date"])
        brief_days = daily_list_sorted[:3]
        if brief_days:
            parts = [f"{x['date']} {x['temp_min']}°~{x['temp_max']}°(강수 {x['precip_max']}%)" for x in brief_days]
            weekly_brief = (
                f"주간 최저 {week_temp_min}° / 최고 {week_temp_max}°, 최대 강수 {week_precip_max}% | 예시: "
                + " / ".join(parts)
            )
        else:
            weekly_brief = f"주간 최저 {week_temp_min}° / 최고 {week_temp_max}°, 최대 강수 {week_precip_max}%"

        return {
            "has_weather": True,
            "week_temp_min": week_temp_min,
            "week_temp_max": week_temp_max,
            "week_precip_max": week_precip_max,
            "week_weather_icon": week_icon,
            "weekly_weather_brief": weekly_brief,
            "daily_weather": daily_list_sorted,
        }

    # -------------------------
    # Daily
    # -------------------------
    def get_daily_data(self, target_date: str) -> Dict[str, Any]:
        # 1) steps
        step_val = int(self.steps_df[self.steps_df["date"] == target_date]["count"].sum()) if not self.steps_df.empty else 0

        # 2) sleep
        sleep_min = 0
        start_hour = None
        if not self.sleep_df.empty:
            day_sleep = self.sleep_df[self.sleep_df["date"] == target_date]
            if not day_sleep.empty:
                sleep_min = int(day_sleep["duration_min"].sum())
                rep = day_sleep.sort_values("duration_min", ascending=False).iloc[0]
                start_hour = _safe_int(rep.get("sleep_start_hour"), None)

        # 3) screen + top apps
        screen_min = 0
        top_3_apps: List[str] = []
        if not self.screen_df.empty:
            day_screen = self.screen_df[self.screen_df["date"] == target_date]
            screen_min = int(day_screen["total_min"].sum()) if not day_screen.empty else 0
            top_apps = (
                day_screen.groupby("packageName")["totalTimeInForeground"]
                .sum()
                .sort_values(ascending=False)
                .head(3)
                if not day_screen.empty
                else pd.Series(dtype=float)
            )
            top_3_apps = [p.split(".")[-1] for p in top_apps.index.tolist()]

        # 4) spending (출금만)
        total_spending = 0
        late_spending = False
        if not self.billing_df.empty:
            day_bills = self.billing_df[self.billing_df["date"] == target_date]
            total_spending = int(day_bills["amount_krw"].sum()) if not day_bills.empty else 0
            if not day_bills.empty:
                late_spending = bool((day_bills["time_kst"].dt.hour >= 22).any())

        # 5) calendar / weather
        today_events = self._get_daily_events(target_date)
        weather_summary = self._get_daily_weather_summary(target_date)

        events_brief = self._calendar_daily_brief(target_date)
        weather_brief = self._weather_daily_brief(target_date)

        return {
            "type": "daily",
            "date": target_date,
            "metrics": {
                "steps": int(step_val),
                "sleep_min": int(sleep_min),
                "sleep_start_hour": start_hour,
                "screen_min": int(screen_min),
                "top_3_apps": top_3_apps,
                "total_spending": int(total_spending),

                # calendar/weather
                "today_events": today_events,
                "today_events_brief": events_brief,
                "today_weather": weather_summary,
                "today_weather_brief": weather_brief,
            },
            "status": {
                "step_eval": "칭찬" if step_val >= 8000 else ("잔소리" if step_val < 5000 else "보통"),
                "sleep_eval": "칭찬" if 420 <= sleep_min < 540 else ("너무많음" if sleep_min >= 540 else ("잔소리" if sleep_min <= 300 else "보통")),
                "sleep_start_eval": "늦게잠" if start_hour is not None and (1 <= start_hour < 5) else "일찍잠",
                "screen_eval": "칭찬" if screen_min <= 120 else ("잔소리" if screen_min >= 240 else "보통"),
                "spending_eval": "과소비" if total_spending >= 50000 else ("절약왕" if total_spending == 0 else "보통"),
                "late_night_snack": late_spending,
            },
        }

    # -------------------------
    # Weekly
    # -------------------------
    def get_weekly_summary(self, start_date: str, end_date: str) -> Dict[str, Any]:
        # steps avg
        avg_steps = 0.0
        if not self.steps_df.empty:
            mask = (self.steps_df["date"] >= start_date) & (self.steps_df["date"] <= end_date)
            daily_steps = self.steps_df[mask].groupby("date")["count"].sum()
            avg_steps = float(daily_steps.mean()) if not daily_steps.empty else 0.0

        # sleep avg (minutes)
        avg_sleep = 0.0
        if not self.sleep_df.empty:
            mask = (self.sleep_df["date"] >= start_date) & (self.sleep_df["date"] <= end_date)
            daily_sleep = self.sleep_df[mask].groupby("date")["duration_min"].sum()
            avg_sleep = float(daily_sleep.mean()) if not daily_sleep.empty else 0.0

        # screen avg (minutes) + most used app
        avg_screen = 0.0
        most_used_app = "없음"
        if not self.screen_df.empty:
            mask = (self.screen_df["date"] >= start_date) & (self.screen_df["date"] <= end_date)
            week_screen = self.screen_df[mask]
            if not week_screen.empty:
                daily_screen = week_screen.groupby("date")["total_min"].sum()
                avg_screen = float(daily_screen.mean()) if not daily_screen.empty else 0.0
                app_sum = week_screen.groupby("packageName")["totalTimeInForeground"].sum()
                if not app_sum.empty:
                    most_used_app = app_sum.idxmax().split(".")[-1]

        # spending total + max/min day
        total_spending = 0
        max_spend = {"amount": 0, "date": "없음"}
        min_spend = {"amount": 0, "date": "없음"}
        if not self.billing_df.empty:
            mask = (self.billing_df["date"] >= start_date) & (self.billing_df["date"] <= end_date)
            week_bills = self.billing_df[mask].copy()
            total_spending = int(week_bills["amount_krw"].sum()) if not week_bills.empty else 0

            daily_spend = week_bills.groupby("date")["amount_krw"].sum() if not week_bills.empty else pd.Series(dtype=float)
            if not daily_spend.empty:
                max_spend = {"amount": int(daily_spend.max()), "date": str(daily_spend.idxmax())}
                min_spend = {"amount": int(daily_spend.min()), "date": str(daily_spend.idxmin())}

        # calendar/weather summary
        cal_sum = self._calendar_weekly_summary(start_date, end_date)
        wx_sum = self._get_weekly_weather_summary(start_date, end_date)

        return {
            "type": "weekly",
            "period": f"{start_date} ~ {end_date}",
            "avg_steps": round(avg_steps, 1),
            "avg_sleep_min": round(avg_sleep, 1),
            "avg_screen_min": int(round(avg_screen, 0)),
            "most_used_app": most_used_app,
            "total_spending": int(total_spending),
            "max_spending": max_spend,
            "min_spending": min_spend,

            "weekly_calendar": cal_sum,
            "weekly_calendar_brief": cal_sum.get("weekly_events_brief", "이번 주 일정 없음"),
            "weekly_weather": wx_sum,
            "weekly_weather_brief": wx_sum.get("weekly_weather_brief", "이번 주 날씨 데이터 없음"),
        }
