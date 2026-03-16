"""
prompt_builder.py
LLM 프롬프트 생성 모듈

핵심 역할:
  - daily_summary / weekly_summary → compact 텍스트 직렬화
  - 이상치 컨텍스트 삽입
  - 강아지 아바타 말투 시스템 프롬프트
  - 난이도별 코인 정책 명시
"""

from src.constants import COIN_REWARD, get_temp_description, ANOMALY_THRESHOLDS
from src.anomaly_detector import AnomalyReport


# ── 강아지 아바타 시스템 프롬프트 ────────────

DOG_SYSTEM_PROMPT = """당신은 사용자의 라이프 코치 강아지 '멍코치'입니다.

[캐릭터 설정]
- 이름: 멍코치 (귀여운 강아지 아바타)
- 말투: 친근하고 따뜻하며, 문장 끝에 자연스럽게 "멍!" 또는 "왈!" 을 붙임
- 성격: 사용자를 진심으로 응원하고 걱정하는 친구 같은 존재
- 평소와 다른 패턴 발견 시: 걱정하는 말투로 먼저 안부를 물어봄
- 퀘스트 제안 시: 신나고 격려하는 말투로 동기부여
- 지출 데이터 있을 시: 과소비면 걱정, 적정 지출이면 칭찬
- 비가 예상될 시: 우산 챙기라고 꼭 언급해줄 것

[말투 예시]
- 일반: "오늘도 열심히 했구나멍! 대단해멍!"
- 걱정: "오늘 잠을 너무 못 잤네... 괜찮아? 멍코치가 걱정돼멍."
- 격려: "이 퀘스트 완료하면 코인 받을 수 있어멍! 같이 해보자멍!"
- 칭찬: "와 오늘 만보나 걸었어?! 최고멍! 왈왈!"

[퀘스트 말투 규칙 — 반드시 지킬 것]
- 퀘스트 description은 반드시 명령형/응원형으로 작성해 (예: "오늘은 10,000보 걸어보자멍!", "스크린타임 4시간 이내로 줄여보자멍!")
- "~해볼까요?", "~할 수 있어요?", "~해보세요" 같은 권유/질문 말투 절대 금지
- 지출 퀘스트는 구체적인 금액 목표(예: 30,000원) 대신 "꼭 필요한 것만 사자멍!", "오늘은 지갑 닫아보자멍!" 같은 행동 지침으로

[퀘스트 코인 시스템]
- Easy  퀘스트: 10코인 (가볍게 달성 가능한 목표)
- Normal퀘스트: 25코인 (적당한 노력 필요)
- Hard  퀘스트: 50코인 (도전적인 목표)
- 회복 Hard 퀘스트: 60코인 (특별 보너스)

[응답 규칙]
- 반드시 JSON 형식으로만 응답 (마크다운 코드블록 없이)
- 한국어만 사용
- 퀘스트/리포트 텍스트는 멍코치 말투로 작성
"""


# ── 요약 텍스트 직렬화 ───────────────────────

def daily_to_text(summary: dict) -> str:
    lines = [f"[{summary['date']} 일간 라이프 데이터]"]

    sl = summary.get("sleep")
    if sl:
        lines.append(f"수면: {sl['bedtime']} 취침 → {sl['wakeup']} 기상 ({sl['duration_hours']}시간)")
    else:
        lines.append("수면: 기록 없음")

    lines.append(f"걸음수: {summary.get('steps', 0):,}보")

    st           = summary.get("screentime", {})
    top3         = st.get("top3_apps", [])
    entertain    = st.get("entertainment_min", 0)
    top3_str     = ", ".join(f"{a['package']} {a['minutes']}분" for a in top3)
    entertain_str = f" (오락성 앱 {entertain}분)" if entertain > 0 else ""
    lines.append(f"스크린타임: 총 {st.get('total_min', 0)}분{entertain_str}")
    if top3_str:
        lines.append(f"  상위3앱: {top3_str}")

    cal = summary.get("calendar", [])
    if cal:
        lines.append("일정: " + ", ".join(f"{e['time']} {e['name']}" for e in cal))
    else:
        lines.append("일정: 없음")

    w = summary.get("weather")
    if w:
        feel = f" (체감 {w['min_feel_temp_c']}~{w['max_feel_temp_c']}°C)" if w.get("min_feel_temp_c") else ""
        humi = f", 습도 {w['avg_humidity_pct']}%" if w.get("avg_humidity_pct") else ""
        rain = " ※ 우산 챙기세요멍!" if w.get("rain_expected") else ""
        lines.append(
            f"날씨: {w['min_temp_c']}~{w['max_temp_c']}°C{feel}{humi}, "
            f"강수확률 {w['max_precip_pct']}%, {' / '.join(w['conditions'])}{rain}"
        )

    sp = summary.get("spending", {})
    if sp.get("total_spent", 0) > 0:
        merchants = ", ".join(sp["top_merchants"][:3]) if sp["top_merchants"] else ""
        lines.append(f"지출: 총 {sp['total_spent']:,}원 (주요: {merchants})")
    else:
        lines.append("지출: 없음")

    return "\n".join(lines)


def weekly_to_text(summary: dict) -> str:
    p = summary["period"]
    lines = [f"[{p['start']} ~ {p['end']} 주간 라이프 데이터]"]

    sl = summary.get("sleep", {})
    if sl:
        lines.append(
            f"수면: 평균 {sl['avg_duration_hours']}h "
            f"(최소 {sl['min_duration_hours']}h / 최대 {sl['max_duration_hours']}h), "
            f"평균 취침 {sl['avg_bedtime']}, 기상 {sl['avg_wakeup']}"
        )

    st = summary.get("steps", {})
    lines.append(
        f"걸음수: 주간 총 {st.get('total', 0):,}보, "
        f"일평균 {st.get('daily_avg', 0):,}보, "
        f"만보 달성 {st.get('days_over_10000', 0)}일"
    )

    sc   = summary.get("screentime", {})
    tops = sc.get("top_apps", [])
    app_str = ", ".join(f"{a['package']} {a['minutes']}분" for a in tops[:5])
    lines.append(f"스크린타임: 일평균 {sc.get('daily_avg_min', 0)}분")
    if app_str:
        lines.append(f"  주간 상위앱: {app_str}")

    cal = summary.get("calendar", {})
    kws = cal.get("keyword_counts", {})
    kw_str = ", ".join(f"{k} {v}회" for k, v in kws.items()) if kws else "없음"
    lines.append(f"일정: 총 {cal.get('total_events', 0)}개 (키워드: {kw_str})")

    w = summary.get("weather", {})
    if w:
        lines.append(
            f"날씨: 평균 {w['avg_min_temp_c']}~{w['avg_max_temp_c']}°C, "
            f"강수확률 {w['avg_precip_pct']}%"
        )

    sp = summary.get("spending", {})
    if sp.get("total_spent", 0) > 0:
        merchants = ", ".join(sp["top_merchants"][:3]) if sp["top_merchants"] else ""
        lines.append(
            f"지출: 주간 총 {sp['total_spent']:,}원, "
            f"일평균 {sp['daily_avg_spent']:,}원 (자주 쓴 곳: {merchants})"
        )
    else:
        lines.append("지출: 기록 없음")

    return "\n".join(lines)


# ── 프롬프트 빌더 ────────────────────────────

class PromptBuilder:

    @staticmethod
    def daily_quest(
        daily_summary: dict,
        anomaly_report: AnomalyReport,
        tomorrow_calendar: list[dict],
        today_calendar: list[dict] | None = None,
        today_weather: dict | None = None,
    ) -> dict:
        data_text    = daily_to_text(daily_summary)
        anomaly_text = anomaly_report.to_prompt_context()
        max_diff     = anomaly_report.recommended_max_difficulty
        tomorrow_str = (
            ", ".join(f"{e['time']} {e['name']}" for e in tomorrow_calendar)
            if tomorrow_calendar else "일정 없음"
        )
        today_str = (
            ", ".join(f"{e['time']} {e['name']}" for e in (today_calendar or []))
            if today_calendar else "일정 없음"
        )

        # 이상치 있을 때 강아지 말투 힌트 추가
        dog_hint = ""
        if anomaly_report.has_anomaly:
            msgs = [a.message for a in anomaly_report.anomalies]
            dog_hint = (
                f"\n[멍코치 걱정 포인트] {' / '.join(msgs)}\n"
                "→ 퀘스트 도입 멘트에서 걱정하는 말투로 먼저 안부를 물어볼 것"
            )

        coin_guide = "\n".join(
            f"  - {d.capitalize()} ({COIN_REWARD[d]}코인): {desc}"
            for d, desc in [
                ("easy",   "가볍게 달성 가능, 회복이 필요한 날 배정"),
                ("normal", "적당한 노력 필요, 일반적인 날 주력 난이도"),
                ("hard",   "도전적 목표, 컨디션 좋은 날 배정"),
            ]
        )

        # 부족한 항목 자동 분석
        sl  = daily_summary.get("sleep", {}) or {}
        st  = daily_summary.get("steps", 0)
        sc  = daily_summary.get("screentime", {}) or {}
        sp  = daily_summary.get("spending", {}) or {}

        weak_points = []
        good_points  = []

        dur = sl.get("duration_hours", 8)
        bedtime_h = sl.get("bedtime_hour", 0)
        if dur < 7:
            weak_points.append(f"수면 부족 ({dur}h — 오늘 목표: 7h 이상)")
        elif dur > 9:
            weak_points.append(f"과수면 ({dur}h — 9h 이하로 줄이기 권장)")
        else:
            good_points.append(f"수면 양호 ({dur}h)")
        # 늦은 취침: 새벽 2시 이후
        if bedtime_h >= 2 and bedtime_h < 12:
            weak_points.append(f"늦은 취침 (새벽 {bedtime_h}시 취침 — 자정 전 취침 권장)")

        if st < 10000:
            weak_points.append(f"걸음수 부족 ({st:,}보 — 오늘 목표: 10,000보)")
        else:
            good_points.append(f"걸음수 충분 ({st:,}보 — 만보 이상, 퀘스트 불필요)")

        ent = sc.get("entertainment_min", 0)
        if ent > 120:
            weak_points.append(f"오락성 앱 과다 ({ent}분 — 오늘 목표: 120분 이내)")

        total_sc = sc.get("total_min", 0)
        if total_sc > 360:
            weak_points.append(f"스크린타임 과다 ({total_sc}분 — 오늘 목표: 360분 이내)")

        spent = sp.get("total_spent", 0)
        if spent > 60000:
            weak_points.append(f"지출 과다 ({spent:,}원 — 오늘은 꼭 필요한 것만 소비하기)")

        weak_str = "\n".join(f"  - {w}" for w in weak_points) if weak_points else "  - 특이사항 없음"
        good_str = "\n".join(f"  + {g}" for g in good_points) if good_points else ""

        # ── 히든 퀘스트 (날씨만) ─────────────────────
        tw = today_weather or {}
        rain_hidden = ""
        if tw.get("rain_expected"):
            precip = tw.get("max_precip_pct", 0)
            rain_hidden = f"오늘 강수확률 {precip}% → 날씨 히든 퀘스트 '우산 챙기기' 반드시 포함 (5코인)"

        # ── 일정 기반 일반 퀘스트 힌트 ──────────────
        schedule_hints = []
        if not today_calendar:
            schedule_hints.append(
                "오늘 일정 없음 → '오늘 할 일 1개 캘린더에 추가하기' 일반 퀘스트 포함 권장"
            )
        early_tomorrow = [e for e in tomorrow_calendar if e.get("time", "99:99") < "10:00"]
        if early_tomorrow:
            earliest = early_tomorrow[0]
            schedule_hints.append(
                f"내일 {earliest['time']}에 '{earliest['name']}' 일정 있음 "
                f"→ '오늘 자정 전 취침하기' 일반 퀘스트 포함 권장"
            )
        schedule_str = "\n".join(f"  - {s}" for s in schedule_hints) if schedule_hints else "  - 없음"

        return {
            "system": DOG_SYSTEM_PROMPT,
            "user": f"""[어제({daily_summary['date']}) 라이프데이터 요약]
{data_text}

[어제 잘한 항목]
{good_str if good_str else "  (없음)"}

[어제 부족했던 항목 — 일반 퀘스트는 이 항목에서 뽑아줘]
{weak_str}

{anomaly_text}
{dog_hint}
[오늘 일정]
{today_str}

[내일 일정]
{tomorrow_str}

[일정 기반 퀘스트 힌트 — 해당하면 일반 퀘스트에 포함]
{schedule_str}

[날씨 히든 퀘스트 조건]
{rain_hidden if rain_hidden else "  없음 (히든 퀘스트 생략)"}

최대 난이도: {max_diff}

위 데이터를 바탕으로 오늘 달성할 퀘스트를 멍코치 말투로 만들어줘.
반드시 아래 규칙을 지켜:
1. 일반 퀘스트: 부족했던 항목 + 일정 힌트 포함해서 총 1~2개
2. 히든 퀘스트: 날씨 히든 퀘스트 조건 있을 때만 추가 (없으면 hidden_quests 빈 배열)
3. description에 어제 수치 직접 언급하며 오늘 목표 구체적으로 제시
4. target_value는 반드시 구체적인 숫자로
5. 일반 퀘스트는 2개 절대 넘기지 마

코인: Easy={COIN_REWARD['easy']}코인 / Normal={COIN_REWARD['normal']}코인 / Hard={COIN_REWARD['hard']}코인 / 히든={COIN_REWARD['hidden']}코인

반드시 아래 JSON 형식으로만 응답:
{{
  "greeting": "어제 데이터 기반 멍코치 안부 1문장",
  "quests": [
    {{
      "id": "q1",
      "category": "수면|운동|스크린타임|생산성|건강|지출|일정",
      "title": "퀘스트 제목 (12자 이내)",
      "description": "어제 수치 언급 + 오늘 목표 멍코치 말투 (45자 이내)",
      "target_value": 반드시 숫자,
      "target_unit": "단위",
      "difficulty": "easy|normal|hard",
      "coin_reward": {COIN_REWARD['easy']}|{COIN_REWARD['normal']}|{COIN_REWARD['hard']},
      "is_recovery": true|false,
      "reason": "추천 이유 (20자 이내)"
    }}
  ],
  "hidden_quests": [
    {{
      "id": "hq1",
      "category": "날씨",
      "title": "히든 퀘스트 제목 (12자 이내)",
      "description": "우산 챙기기 관련 멍코치 말투 (40자 이내)",
      "target_value": 1,
      "target_unit": "회",
      "difficulty": "hidden",
      "coin_reward": {COIN_REWARD['hidden']}
    }}
  ]
}}"""
        }

    @staticmethod
    def weekly_quest(
        weekly_summary: dict,
        anomaly_reports: list[AnomalyReport],
    ) -> dict:
        data_text = weekly_to_text(weekly_summary)

        # 주간 이상치 요약
        total_anomalies = sum(len(r.anomalies) for r in anomaly_reports)
        anomaly_days    = sum(1 for r in anomaly_reports if r.has_anomaly)
        worst_sev       = "critical" if any(
            r.worst_severity == "critical" for r in anomaly_reports
        ) else ("warning" if anomaly_days > 2 else "mild" if anomaly_days > 0 else None)

        anomaly_summary = (
            f"주간 이상치: {anomaly_days}일 감지 (총 {total_anomalies}건), "
            f"최고 심각도: {worst_sev or '없음'}"
        )

        # 주간 부족 항목 자동 분석
        wsl  = weekly_summary.get("sleep", {})
        wst  = weekly_summary.get("steps", {})
        wsc  = weekly_summary.get("screentime", {})
        wsp  = weekly_summary.get("spending", {})

        weak_weekly = []

        # 수면: 7h 미만 부족 / 9h 초과 과수면 / 새벽 2시 이후 늦은 취침
        avg_dur = wsl.get("avg_duration_hours", 8)
        avg_bed = wsl.get("avg_bedtime", "00:00")
        if avg_dur < 7:
            weak_weekly.append(f"수면 부족 (평균 {avg_dur}h — 7h 이상 권장)")
        elif avg_dur > 9:
            weak_weekly.append(f"과수면 (평균 {avg_dur}h — 9h 이하 권장)")
        avg_bed_h = int(avg_bed[:2]) if avg_bed else 0
        if avg_bed_h >= 2 and avg_bed_h < 12:
            weak_weekly.append(f"늦은 취침 (평균 취침 {avg_bed} — 자정 전 취침 권장)")

        # 걸음수: 만보 주 3일 미만
        if wst.get("days_over_10000", 0) < 3:
            weak_weekly.append(f"만보 달성 부족 ({wst.get('days_over_10000')}일 — 주 3일 목표)")

        # 스크린타임: 일평균 360분(6h) 초과
        if wsc.get("daily_avg_min", 0) > 360:
            weak_weekly.append(f"스크린타임 과다 (일평균 {wsc.get('daily_avg_min')}분 — 6시간 초과)")

        # 지출: 일평균 6만원 초과
        if wsp.get("daily_avg_spent", 0) > 60000:
            weak_weekly.append(f"지출 과다 (일평균 {wsp.get('daily_avg_spent'):,}원 — 6만원 초과)")

        # 일정: 일평균 3개 미만 / 공부 일정 없음
        wcal = weekly_summary.get("calendar", {})
        total_ev = wcal.get("total_events", 0)
        days_cnt = weekly_summary.get("days_count", 7)
        daily_avg_ev = round(total_ev / days_cnt, 1) if days_cnt else 0
        kw = wcal.get("keyword_counts", {})
        if daily_avg_ev < 3:
            weak_weekly.append(f"일정 부족 (일평균 {daily_avg_ev}개 — 하루 3개 이상 목표 설정 권장)")
        if not kw.get("스터디") and not kw.get("공부"):
            weak_weekly.append("공부/스터디 일정 없음 — 이번 주 공부 일정 1개 추가 권장")

        weak_weekly_str = "\n".join(f"  - {w}" for w in weak_weekly) if weak_weekly else "  - 특이사항 없음"


        return {
            "system": DOG_SYSTEM_PROMPT,
            "user": f"""[지난 주({weekly_summary['period']['start']} ~ {weekly_summary['period']['end']}) 라이프데이터 요약]
{data_text}

[지난 주 부족했던 항목]
{weak_weekly_str}

{anomaly_summary}

위 지난 주 데이터를 바탕으로 이번 주 달성할 퀘스트 3개를 멍코치 말투로 만들어줘.
반드시 아래 규칙을 지켜:
1. 부족했던 항목들 중에서 3가지를 골라 퀘스트를 뽑아줘 (부족 항목이 3개 미만이면 성장 퀘스트로 채워줘)
2. description에 지난 주 수치를 직접 언급하며 이번 주 목표를 구체적으로 제시해 (예: "지난주 만보 달성 2일이었으니 이번 주는 4일 도전멍!")
3. target_value는 반드시 구체적인 숫자로
4. 퀘스트는 반드시 3개

코인: Easy={COIN_REWARD['easy']}코인 / Normal={COIN_REWARD['normal']}코인 / Hard={COIN_REWARD['hard']}코인

반드시 아래 JSON 형식으로만 응답:
{{
  "weekly_greeting": "지난 주 데이터 기반 총평 멍코치 말투 1문장 (수치 직접 언급)",
  "quests": [
    {{
      "id": "wq1",
      "category": "수면|운동|스크린타임|생산성|건강|지출",
      "title": "주간 퀘스트 제목 (12자 이내)",
      "description": "지난 주 수치 언급 + 이번 주 목표 멍코치 말투 (50자 이내)",
      "target_value": 반드시 숫자,
      "target_unit": "단위",
      "difficulty": "easy|normal|hard",
      "coin_reward": {COIN_REWARD['easy']}|{COIN_REWARD['normal']}|{COIN_REWARD['hard']},
      "reason": "지난 주 데이터 기반 추천 이유 (20자 이내)"
    }}
  ]
}}"""
        }

    @staticmethod
    def daily_report(
        daily_summary: dict,
        anomaly_report: AnomalyReport,
        tomorrow_weather: dict | None = None,
    ) -> dict:
        data_text    = daily_to_text(daily_summary)
        anomaly_text = anomaly_report.to_prompt_context()

        # 내일 날씨 — 기온 해석을 코드에서 직접 처리
        tw = tomorrow_weather or {}
        if tw:
            feel_max   = tw.get("max_feel_temp_c") or tw.get("max_temp_c", 0)
            temp_desc  = get_temp_description(feel_max)
            rain_str   = " 우산 필요!" if tw.get("rain_expected") else ""
            tomorrow_str = (
                f"{tw.get('min_temp_c')}~{tw.get('max_temp_c')}°C "
                f"(체감 {tw.get('min_feel_temp_c')}~{tw.get('max_feel_temp_c')}°C), "
                f"강수확률 {tw.get('max_precip_pct')}%, {temp_desc}{rain_str}"
            )
        else:
            tomorrow_str = "날씨 정보 없음"

        return {
            "system": DOG_SYSTEM_PROMPT,
            "user": f"""{data_text}

{anomaly_text}

위 데이터를 멍코치 말투로 항목별로 분석해서 오늘 하루 리포트를 작성해줘.
각 항목(수면/걸음수/스크린타임/지출/일정)마다 데이터를 직접 언급하며 잘한 점은 칭찬, 부족한 점은 간단한 피드백을 줘.

반드시 아래 JSON 형식으로만 응답:
{{
  "overall_score": 0~100 정수,
  "dog_comment": "멍코치 하루 총평 1~2문장",
  "items": {{
    "sleep": {{
      "score": 0~100 정수,
      "data": "취침/기상 시각과 수면시간 그대로 언급",
      "feedback": "7h 미만이면 부족 피드백 / 9h 초과면 줄이기 피드백 / 새벽 2시 이후 취침이면 늦은 취침 피드백 / 정상이면 칭찬 멍코치 말투 (30자 이내)"
    }},
    "steps": {{
      "score": 0~100 정수,
      "data": "걸음수 숫자 직접 언급",
      "feedback": "만보 달성 여부 기준 피드백 멍코치 말투 (30자 이내)"
    }},
    "screentime": {{
      "score": 0~100 정수,
      "data": "총 사용시간과 상위 앱 언급",
      "feedback": "오락성 앱 많으면 줄이라고 피드백, 적당하면 칭찬 멍코치 말투 (30자 이내)"
    }},
    "spending": {{
      "score": 0~100 정수,
      "data": "총 지출금액과 주요 지출처 언급",
      "feedback": "과소비면 걱정, 적당하면 칭찬 멍코치 말투 (30자 이내)"
    }},
    "schedule": {{
      "score": 0~100 정수,
      "data": "오늘 일정 언급",
      "feedback": "일정 소화 여부 피드백 멍코치 말투 (30자 이내)"
    }}
  }},
  "anomaly_alert": "평소와 달랐던 점 멍코치 말투로 걱정하며 언급 (있을 때만, 없으면 null)",
  "tomorrow_weather": "{tomorrow_str}",
  "tomorrow_comment": "내일 날씨 설명하며 준비 팁 멍코치 말투 (40자 이내)"
}}"""
        }

    @staticmethod
    def weekly_report(
        weekly_summary: dict,
        anomaly_reports: list[AnomalyReport],
    ) -> dict:
        data_text    = weekly_to_text(weekly_summary)
        anomaly_days = sum(1 for r in anomaly_reports if r.has_anomaly)
        anomaly_text = f"컨디션 저조 일수: {anomaly_days}일 / {weekly_summary['days_count']}일"

        # 지출 수치 명시
        sp           = weekly_summary.get("spending", {})
        total_spent  = sp.get("total_spent", 0)
        daily_avg    = sp.get("daily_avg_spent", 0)
        merchants    = ", ".join(sp.get("top_merchants", [])[:3])
        overspend_thr = ANOMALY_THRESHOLDS["spending"]["overspend_threshold"]
        if total_spent > 0:
            overspend_flag = "과소비 주의!" if daily_avg > overspend_thr else "적정 지출 수준"
            spending_hint = (
                f"[지출 분석용] 주간 총 지출 {total_spent:,}원, "
                f"일평균 {daily_avg:,}원 (과소비 기준: 일 {overspend_thr:,}원), "
                f"자주 쓴 곳: {merchants} → {overspend_flag}"
            )
        else:
            spending_hint = "[지출 분석용] 이번 주 지출 기록 없음"

        return {
            "system": DOG_SYSTEM_PROMPT,
            "user": f"""{data_text}

{anomaly_text}
{spending_hint}

위 주간 데이터를 멍코치 말투로 항목별로 분석해서 주간 리포트를 작성해줘.
각 항목마다 이번 주 데이터를 직접 언급하며 잘한 점은 칭찬, 부족한 점은 간단한 피드백을 줘.
지출 항목은 반드시 주간 총액, 일평균, 자주 쓴 곳을 data에 직접 써줘.

반드시 아래 JSON 형식으로만 응답:
{{
  "overall_score": 0~100 정수,
  "dog_comment": "이번 주 총평 멍코치 말투 1~2문장",
  "items": {{
    "sleep": {{
      "data": "평균 수면시간, 평균 취침/기상 시각 직접 언급",
      "feedback": "평균 7h 미만이면 부족 피드백 / 9h 초과면 줄이기 피드백 / 평균 취침이 새벽 2시 이후면 늦은 취침 피드백 / 정상이면 칭찬 멍코치 말투 (40자 이내)"
    }},
    "steps": {{
      "data": "주간 총 걸음수, 일평균, 만보 달성일수 직접 언급",
      "feedback": "피드백 멍코치 말투 (40자 이내)"
    }},
    "screentime": {{
      "data": "일평균 스크린타임, 자주 쓴 앱 언급",
      "feedback": "오락성 앱 많으면 줄이라고 피드백 멍코치 말투 (40자 이내)"
    }},
    "spending": {{
      "data": "주간 총 지출과 일평균 지출 금액, 자주 쓴 곳 반드시 직접 언급. 지출 기록 없으면 '지출 기록 없음'",
      "feedback": "지출이 많으면 과소비 걱정, 적당하면 칭찬. 지출 기록 없으면 null"
    }},
    "schedule": {{
      "data": "총 일정 수, 주요 활동 언급",
      "feedback": "활동량 피드백 멍코치 말투 (40자 이내)"
    }}
  }},
  "best_day": "가장 좋았던 날짜",
  "anomaly_summary": "컨디션 저조했던 날 멍코치 말투로 언급 (있을 때만, 없으면 null)",
  "next_week_advice": "다음 주 응원 + 개선 포인트 멍코치 말투 (50자 이내)"
}}"""
        }
