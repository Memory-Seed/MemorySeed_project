# analyzer.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, List, Any

import json
import re

import numpy as np
import pandas as pd
from statsmodels.tsa.seasonal import STL


def _to_kst(dt_like) -> pd.Timestamp:
    """Parse datetime-like to Asia/Seoul tz-aware Timestamp."""
    ts = pd.to_datetime(dt_like, utc=True, errors="coerce")
    if pd.isna(ts):
        ts = pd.to_datetime(dt_like, errors="coerce")
        if pd.isna(ts):
            raise ValueError(f"Cannot parse datetime: {dt_like}")
        if ts.tzinfo is None:
            ts = ts.tz_localize("Asia/Seoul")
        return ts.tz_convert("Asia/Seoul")
    return ts.tz_convert("Asia/Seoul")


def _ensure_daily_series(
    s: pd.Series,
    start: Optional[pd.Timestamp] = None,
    end: Optional[pd.Timestamp] = None,
) -> pd.Series:
    """Ensure daily frequency with missing days filled with 0."""
    if s is None or len(s) == 0:
        return pd.Series(dtype=float)
    s = s.sort_index()
    if start is None:
        start = s.index.min()
    if end is None:
        end = s.index.max()
    idx = pd.date_range(start=start, end=end, freq="D", tz="Asia/Seoul")
    return s.reindex(idx).fillna(0)


@dataclass
class AnomalyResult:
    date: str
    metric: str
    actual_value: float
    z_score: float
    is_anomaly: bool
    trend: float
    is_higher: bool


class LifeLogAnalyzer:
    """
    JSON 기반 라이프로그 이상치 분석기.
    - steps.json: [{count, startTime, endTime, ...}, ...]
    - sleep.json: [{startTime, endTime, ...}, ...]
    - screentime.json: [{packageName, firstTimeStamp, totalTimeInForeground, ...}, ...]
    - notification.json: NDJSON lines
        - postTime(ms) 우선, isoTime fallback
        - extras.android.text / extras.android.bigText에서 '출금 N원'만 지출로 카운트
    """

    def __init__(
        self,
        steps_path: str,
        sleep_path: str,
        screen_path: str,
        billing_path: str,
        tz: str = "Asia/Seoul",
    ):
        self.tz = tz
        self.df_steps = self._load_steps_daily(steps_path)
        self.df_sleep = self._load_sleep_daily(sleep_path)
        self.df_screen = self._load_screen_daily(screen_path)
        self.df_billing = self._load_billing_daily(billing_path)

        series_list = [self.df_steps, self.df_sleep, self.df_screen, self.df_billing]
        starts = [s.index.min() for s in series_list if s is not None and len(s) > 0]
        ends = [s.index.max() for s in series_list if s is not None and len(s) > 0]
        if starts and ends:
            start = min(starts)
            end = max(ends)
            self.df_steps = _ensure_daily_series(self.df_steps, start, end)
            self.df_sleep = _ensure_daily_series(self.df_sleep, start, end)
            self.df_screen = _ensure_daily_series(self.df_screen, start, end)
            self.df_billing = _ensure_daily_series(self.df_billing, start, end)
        else:
            self.df_steps = _ensure_daily_series(self.df_steps)
            self.df_sleep = _ensure_daily_series(self.df_sleep)
            self.df_screen = _ensure_daily_series(self.df_screen)
            self.df_billing = _ensure_daily_series(self.df_billing)

    # -----------------
    # Loaders
    # -----------------
    def _load_steps_daily(self, path: str) -> pd.Series:
        df = pd.read_json(path)
        if df.empty:
            return pd.Series(dtype=float)
        df["start_kst"] = df["startTime"].apply(_to_kst)
        df["date"] = df["start_kst"].dt.floor("D")
        daily = df.groupby("date")["count"].sum()
        daily.index = daily.index.tz_convert("Asia/Seoul")
        daily.name = "steps"
        return daily.astype(float)

    def _load_sleep_daily(self, path: str) -> pd.Series:
        df = pd.read_json(path)
        if df.empty:
            return pd.Series(dtype=float)
        df["start_kst"] = df["startTime"].apply(_to_kst)
        df["end_kst"] = df["endTime"].apply(_to_kst)
        df["duration_min"] = (df["end_kst"] - df["start_kst"]).dt.total_seconds() / 60.0
        df["date"] = df["end_kst"].dt.floor("D")  # 기상 날짜 기준
        daily = df.groupby("date")["duration_min"].sum()
        daily.index = daily.index.tz_convert("Asia/Seoul")
        daily.name = "sleep_min"
        return daily.astype(float)

    def _load_screen_daily(self, path: str) -> pd.Series:
        df = pd.read_json(path)
        if df.empty:
            return pd.Series(dtype=float)
        df["start_kst"] = pd.to_datetime(df["firstTimeStamp"], unit="ms", utc=True, errors="coerce").dt.tz_convert("Asia/Seoul")
        df["date"] = df["start_kst"].dt.floor("D")
        df["total_min"] = df["totalTimeInForeground"] / (1000.0 * 60.0)
        daily = df.groupby("date")["total_min"].sum()
        daily.index = daily.index.tz_convert("Asia/Seoul")
        daily.name = "screen_min"
        return daily.astype(float)

    def _load_billing_daily(self, path: str) -> pd.Series:
        """
        notification NDJSON에서 일별 출금 합계를 만들기
        """
        rows: List[Dict[str, Any]] = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

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

        if not rows:
            return pd.Series(dtype=float)

        df = pd.json_normalize(rows)

        # time: postTime(ms) 우선
        if "postTime" in df.columns:
            df["time_kst"] = pd.to_datetime(df["postTime"], unit="ms", utc=True, errors="coerce").dt.tz_convert("Asia/Seoul")
        elif "isoTime" in df.columns:
            time_kst = pd.to_datetime(df["isoTime"], errors="coerce")
            if time_kst.dt.tz is None:
                time_kst = time_kst.dt.tz_localize("Asia/Seoul")
            else:
                time_kst = time_kst.dt.tz_convert("Asia/Seoul")
            df["time_kst"] = time_kst
        else:
            return pd.Series(dtype=float)

        df = df.dropna(subset=["time_kst"])
        if df.empty:
            return pd.Series(dtype=float)

        text_series = df.get("extras.android.text", pd.Series([""] * len(df)))
        big_series = df.get("extras.android.bigText", pd.Series([""] * len(df)))

        money_re = re.compile(r"(출금|입금)\s*([0-9][0-9,]*)\s*원")

        def parse_spend(text: Any, big: Any) -> float:
            t = ""
            if isinstance(text, str):
                t += text
            if isinstance(big, str) and big.strip():
                t += "\n" + big
            if not t:
                return 0.0

            m = money_re.search(t)
            if not m:
                return 0.0
            kind = m.group(1)
            amt = float(int(m.group(2).replace(",", "")))
            return amt if kind == "출금" else 0.0

        df["spend_krw"] = [parse_spend(t, b) for t, b in zip(text_series.tolist(), big_series.tolist())]
        df["date"] = df["time_kst"].dt.floor("D")

        daily = df.groupby("date")["spend_krw"].sum()
        daily.index = daily.index.tz_convert("Asia/Seoul")
        daily.name = "spending_krw"
        return daily.astype(float)

    # -----------------
    # Anomaly detection
    # -----------------
    def analyze_anomaly(self, metric_type: str, target_date: str, period: int = 7, z_thresh: float = 2.5) -> Dict[str, Any]:
        """
        metric_type: 'steps' | 'sleep' | 'screen' | 'billing'
        """
        series_map = {
            "steps": self.df_steps,
            "sleep": self.df_sleep,
            "screen": self.df_screen,
            "billing": self.df_billing,
        }
        series = series_map.get(metric_type)
        if series is None or len(series) < 14:
            return {"is_anomaly": False, "reason": "데이터 부족"}

        target_dt = pd.to_datetime(target_date, errors="coerce")
        if pd.isna(target_dt):
            return {"is_anomaly": False, "reason": "잘못된 날짜 포맷"}

        if target_dt.tzinfo is None:
            target_dt = target_dt.tz_localize("Asia/Seoul")
        else:
            target_dt = target_dt.tz_convert("Asia/Seoul")
        target_dt = target_dt.floor("D")

        if target_dt not in series.index:
            return {"is_anomaly": False, "reason": "해당 날짜 데이터 없음"}

        stl = STL(series, period=period, robust=True)
        result = stl.fit()
        resid = result.resid
        mu = float(resid.mean())
        sigma = float(resid.std())
        if sigma == 0.0:
            sigma = 1.0

        z_score = float((resid.loc[target_dt] - mu) / sigma)
        is_anomaly = abs(z_score) > z_thresh

        return {
            "date": target_date,
            "metric": metric_type,
            "actual_value": float(series.loc[target_dt]),
            "z_score": round(z_score, 2),
            "is_anomaly": bool(is_anomaly),
            "trend": round(float(result.trend.loc[target_dt]), 2),
            "is_higher": bool(z_score > 0),
        }

    def analyze_anomaly_multi(self, target_date: str, metrics: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        if metrics is None:
            metrics = ["steps", "sleep", "screen", "billing"]
        return [self.analyze_anomaly(m, target_date) for m in metrics]
