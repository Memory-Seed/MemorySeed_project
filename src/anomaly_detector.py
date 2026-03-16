"""
anomaly_detector.py
이상치 탐지 모듈

탐지 방식 2가지를 조합:
  1. Rule-based  : 절대 기준값 (수면 4h 미만, 스크린타임 6h 초과 등)
  2. IQR-based   : 사용자 본인의 7~30일 히스토리 대비 통계적 이탈

결과 AnomalyReport 는 LLM 프롬프트 빌더에 컨텍스트로 전달됨
  → 강아지가 이상치를 인식하고 말투/퀘스트 난이도를 조정
"""

from dataclasses import dataclass, field
from typing import Optional
import statistics

from src.constants import ANOMALY_THRESHOLDS, ANOMALY_SEVERITY_TO_DIFFICULTY


# ── 데이터클래스 ─────────────────────────────

@dataclass
class Anomaly:
    category:  str          # "sleep" | "steps" | "screentime"
    metric:    str          # "duration_hours" | "total_steps" | ...
    severity:  str          # "critical" | "warning" | "mild"
    direction: str          # "low" | "high"
    actual:    float
    expected:  str          # "평균 7.2h" 같은 사람이 읽을 수 있는 기대값 문자열
    message:   str          # 강아지 말투용 한 줄 설명


@dataclass
class AnomalyReport:
    date:       str
    anomalies:  list[Anomaly] = field(default_factory=list)

    @property
    def has_anomaly(self) -> bool:
        return len(self.anomalies) > 0

    @property
    def worst_severity(self) -> Optional[str]:
        if not self.anomalies:
            return None
        order = ["critical", "warning", "mild"]
        for sev in order:
            if any(a.severity == sev for a in self.anomalies):
                return sev
        return None

    @property
    def recommended_max_difficulty(self) -> str:
        """
        이상치 심각도에 따라 퀘스트 최대 난이도 결정
        critical → 오늘은 easy만 / warning → normal까지 / mild → hard 가능
        """
        mapping = {"critical": "easy", "warning": "normal", "mild": "hard"}
        return mapping.get(self.worst_severity or "", "hard")

    def to_prompt_context(self) -> str:
        """LLM 프롬프트에 삽입할 이상치 요약 텍스트"""
        if not self.has_anomaly:
            return "평소와 비슷한 하루 (특이사항 없음)"
        lines = ["[평소와 다른 패턴 감지]"]
        for a in self.anomalies:
            lines.append(f"  - [{a.severity.upper()}] {a.message} (실제: {a.actual}, 기대: {a.expected})")
        lines.append(f"  → 오늘 퀘스트 최대 난이도: {self.recommended_max_difficulty} (컨디션 기반 자동 조정)")
        return "\n".join(lines)


# ── 메인 탐지기 ──────────────────────────────

class AnomalyDetector:
    """
    daily_summary dict + 히스토리(daily_summary list) 를 받아
    AnomalyReport 반환

    사용법:
        detector = AnomalyDetector(history=weekly_summary["daily_list"])
        report   = detector.detect(today_summary)
    """

    def __init__(self, history: list[dict] | None = None):
        """
        history: 최근 N일치 daily_summary 리스트 (통계 기준선 계산용)
                 None 이면 rule-based 탐지만 수행
        """
        self.history = history or []

    def detect(self, daily: dict) -> AnomalyReport:
        report = AnomalyReport(date=daily["date"])

        report.anomalies += self._detect_sleep(daily.get("sleep"))
        report.anomalies += self._detect_steps(daily.get("steps", 0))
        report.anomalies += self._detect_screentime(daily.get("screentime", {}))
        report.anomalies += self._detect_spending(daily.get("spending", {}))

        return report

    # ── 수면 탐지 ────────────────────────────

    def _detect_sleep(self, sleep: Optional[dict]) -> list[Anomaly]:
        anomalies = []
        if not sleep:
            return anomalies

        dur  = sleep["duration_hours"]
        thr  = ANOMALY_THRESHOLDS["sleep"]
        hist = self._sleep_history_durations()
        avg  = round(statistics.mean(hist), 1) if hist else None
        expected_str = f"권장 {thr['min_hours']}~{thr['max_hours']}h"

        # 수면 부족 (7h 미만)
        if dur < thr["min_hours"]:
            severity = "critical" if dur < thr["anomaly_min_hours"] else "warning"
            anomalies.append(Anomaly(
                category="sleep", metric="duration_hours",
                severity=severity, direction="low",
                actual=dur, expected=expected_str,
                message=f"수면이 {dur}시간으로 부족해요 (권장 7h 이상)",
            ))

        # 과수면 (9h 초과)
        elif dur > thr["max_hours"]:
            anomalies.append(Anomaly(
                category="sleep", metric="duration_hours",
                severity="mild", direction="high",
                actual=dur, expected=expected_str,
                message=f"수면이 {dur}시간으로 너무 많아요 (권장 9h 이하)",
            ))

        # 늦은 취침 (새벽 2시 이후)
        bedtime_h = sleep.get("bedtime_hour", 0)
        if bedtime_h >= thr["late_bedtime_hour"] and bedtime_h < 12:
            anomalies.append(Anomaly(
                category="sleep", metric="bedtime",
                severity="warning", direction="high",
                actual=bedtime_h, expected=f"새벽 {thr['late_bedtime_hour']}시 이전",
                message=f"새벽 {bedtime_h}시에 잠들었어요 — 취침 시각이 너무 늦어요",
            ))

        return anomalies

    # ── 걸음수 탐지 ──────────────────────────

    def _detect_steps(self, steps: int) -> list[Anomaly]:
        anomalies = []
        thr  = ANOMALY_THRESHOLDS["steps"]
        hist = self._steps_history()
        avg  = round(statistics.mean(hist)) if hist else None
        expected_str = f"평균 {avg:,}보" if avg else "기준 없음"

        if steps < thr["low_threshold"]:
            severity = "critical" if steps < 300 else "warning"
            anomalies.append(Anomaly(
                category="steps", metric="total_steps",
                severity=severity, direction="low",
                actual=steps, expected=expected_str,
                message=f"오늘 걸음수가 {steps:,}보로 거의 안 움직였어요",
            ))

        elif len(hist) >= 7:
            iqr_anomaly = self._iqr_check(
                value=steps, data=hist,
                category="steps", metric="total_steps",
                label="걸음수",
            )
            if iqr_anomaly:
                anomalies.append(iqr_anomaly)

        return anomalies

    # ── 스크린타임 탐지 ──────────────────────

    def _detect_screentime(self, screentime: dict) -> list[Anomaly]:
        anomalies = []
        if not screentime:
            return anomalies

        thr   = ANOMALY_THRESHOLDS["screentime"]
        total = screentime.get("total_min", 0)
        hist  = self._screentime_history()
        avg    = round(statistics.mean(hist)) if hist else None
        expected_str = f"평균 {avg}분" if avg else "기준 없음"

        # 총 스크린타임
        if total > thr["max_total_min"]:
            severity = "critical" if total > 480 else "warning"
            anomalies.append(Anomaly(
                category="screentime", metric="total_min",
                severity=severity, direction="high",
                actual=total, expected=expected_str,
                message=f"스크린타임이 {total}분({total//60}시간)으로 너무 많아요",
            ))

        # 오락성 앱 (게임/유튜브/웹툰 등) 과다 사용
        entertainment_min = screentime.get("entertainment_min", 0)
        if entertainment_min > thr["max_entertainment"]:
            top3 = screentime.get("top3_apps", [])
            top3_str = ", ".join(a["package"].split(".")[-1] for a in top3[:2])
            severity = "warning" if entertainment_min > 180 else "mild"
            anomalies.append(Anomaly(
                category="screentime", metric="entertainment_min",
                severity=severity, direction="high",
                actual=entertainment_min,
                expected=f"{thr['max_entertainment']}분 이내",
                message=f"게임/유튜브 등 오락 앱을 {entertainment_min}분이나 사용했어요 ({top3_str})",
            ))

        # IQR 기반 (총 스크린타임)
        if total <= thr["max_total_min"] and len(hist) >= 7:
            iqr_anomaly = self._iqr_check(
                value=total, data=hist,
                category="screentime", metric="total_min",
                label="스크린타임",
            )
            if iqr_anomaly:
                anomalies.append(iqr_anomaly)

        return anomalies

    # ── 지출 탐지 ────────────────────────────

    def _detect_spending(self, spending: dict) -> list[Anomaly]:
        anomalies = []
        if not spending:
            return anomalies
        total = spending.get("total_spent", 0)
        thr   = ANOMALY_THRESHOLDS.get("spending", {}).get("overspend_threshold", 60000)
        if total > thr:
            severity = "warning" if total > thr * 2 else "mild"
            merchants = ", ".join(spending.get("top_merchants", [])[:2])
            anomalies.append(Anomaly(
                category="spending", metric="total_spent",
                severity=severity, direction="high",
                actual=total, expected=f"{thr:,}원 이내",
                message=f"오늘 {total:,}원 지출했어요 ({merchants}) — 기준 {thr:,}원 초과",
            ))
        return anomalies

    # ── IQR 공통 로직 ────────────────────────

    def _iqr_check(
        self,
        value: float,
        data: list[float],
        category: str,
        metric: str,
        label: str,
        k: float = 1.5,
    ) -> Optional[Anomaly]:
        """
        IQR 방식: Q1 - k*IQR ~ Q3 + k*IQR 범위 벗어나면 이상치
        k=1.5 (일반적) / k=3.0 (극단치)
        """
        sorted_data = sorted(data)
        n = len(sorted_data)
        q1 = sorted_data[n // 4]
        q3 = sorted_data[(3 * n) // 4]
        iqr = q3 - q1

        lower = q1 - k * iqr
        upper = q3 + k * iqr
        avg   = round(statistics.mean(data), 1)

        if value < lower:
            return Anomaly(
                category=category, metric=metric,
                severity="mild", direction="low",
                actual=value,
                expected=f"평균 {avg} (정상범위 {round(lower,1)}~{round(upper,1)})",
                message=f"{label}이 평소보다 훨씬 낮아요",
            )
        if value > upper:
            return Anomaly(
                category=category, metric=metric,
                severity="mild", direction="high",
                actual=value,
                expected=f"평균 {avg} (정상범위 {round(lower,1)}~{round(upper,1)})",
                message=f"{label}이 평소보다 훨씬 높아요",
            )
        return None

    # ── 히스토리 추출 헬퍼 ───────────────────

    def _sleep_history_durations(self) -> list[float]:
        return [
            d["sleep"]["duration_hours"]
            for d in self.history
            if d.get("sleep")
        ]

    def _steps_history(self) -> list[float]:
        return [float(d["steps"]) for d in self.history if d.get("steps") is not None]

    def _screentime_history(self) -> list[float]:
        return [
            float(d["screentime"]["total_min"])
            for d in self.history
            if d.get("screentime")
        ]
