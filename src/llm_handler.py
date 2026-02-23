# llm_handler.py
from __future__ import annotations

import os
import random
from typing import Dict, Any, List, Optional

import pandas as pd
from openai import OpenAI


class QwenAnalyst:
    """
    Ollama(OpenAI-compatible) Qwen 모델을 사용해:
    - 일일/주간 리포트 생성
    - 일일 퀘스트(1~2개) 생성
    - 주간 퀘스트(1개) 생성
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ):
        self.client = OpenAI(
            base_url=base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1"),
            api_key=api_key or os.getenv("OLLAMA_API_KEY", "ollama"),
        )
        self.model = model or os.getenv("OLLAMA_MODEL", "qwen2.5:7b")

    # -------------------------
    # Helpers
    # -------------------------
    def format_time(self, minutes: int) -> str:
        """분을 'X시간 X분' 형식으로 변환"""
        minutes = abs(int(minutes))
        if minutes < 60:
            return f"0시간 {minutes}분"
        h = minutes // 60
        mins = minutes % 60
        return f"{h}시간 {mins}분"

    def _calc_days_from_period(self, period_str: Optional[str]) -> int:
        """
        "YYYY-MM-DD ~ YYYY-MM-DD" 형태에서 inclusive day count 계산.
        실패하면 7로 fallback.
        """
        if not period_str or "~" not in period_str:
            return 7
        try:
            a, b = [x.strip() for x in period_str.split("~")]
            days = (pd.to_datetime(b) - pd.to_datetime(a)).days + 1
            return days if days > 0 else 7
        except Exception:
            return 7

    # -------------------------
    # Report (daily/weekly)
    # -------------------------
    def analyze(self, data: Dict[str, Any], anomaly_results: Optional[List[Dict[str, Any]]] = None) -> str:
        # ✅ metrics payload 형태 방어
        mode = data.get("type", "daily")
        metrics = data["metrics"] if ("metrics" in data and isinstance(data["metrics"], dict)) else data

        raw_date = data.get("date", "")
        if raw_date:
            try:
                date_obj = pd.to_datetime(raw_date)
                display_date = f"{date_obj.month}월 {date_obj.day}일"
            except Exception:
                display_date = raw_date
        else:
            display_date = "오늘"

        # 1) STL 이상치 정리
        anomaly_summary = ""
        if anomaly_results:
            metric_names = {
                "steps": "걸음수",
                "sleep": "수면 시간",
                "screen": "폰 사용 시간",
                "billing": "지출 금액",
            }

            if mode == "weekly":
                # ✅ period 기반으로 days 계산
                days = self._calc_days_from_period(metrics.get("period"))
                avg_spending_per_day = (metrics.get("total_spending", 0) or 0) / max(days, 1)

                avg_ref = {
                    "steps": metrics.get("avg_steps", 0),
                    "sleep": metrics.get("avg_sleep_min", 0),
                    "screen": metrics.get("avg_screen_min", 0),
                    "billing": avg_spending_per_day,
                }

                for res in anomaly_results:
                    if res.get("is_anomaly"):
                        res_date = pd.to_datetime(res["date"])
                        dt_kor = f"{res_date.month}월 {res_date.day}일"

                        m_key = res["metric"]
                        m_label = metric_names.get(m_key, m_key)
                        actual = res["actual_value"]
                        avg_val = avg_ref.get(m_key, 0)
                        diff = abs(actual - avg_val)

                        if m_key == "steps":
                            act_s, avg_s, diff_s = f"{int(actual)}보", f"{int(avg_val)}보", f"{int(diff)}보"
                        elif m_key in ["sleep", "screen"]:
                            act_s, avg_s, diff_s = (
                                self.format_time(int(actual)),
                                self.format_time(int(avg_val)),
                                self.format_time(int(diff)),
                            )
                        else:  # billing
                            act_s, avg_s, diff_s = f"{int(actual)}원", f"{int(avg_val)}원", f"{int(diff)}원"

                        direction = "많음(Over)" if res["is_higher"] else "적음(Under)"
                        anomaly_summary += (
                            f"- {dt_kor}: {m_label}가 {act_s}로, 이번 주 평균({avg_s})보다 {diff_s}이나 더 {direction}! "
                        )

            else:
                for res in anomaly_results:
                    if res.get("is_anomaly"):
                        res_date = pd.to_datetime(res["date"])
                        dt_kor = f"{res_date.month}월 {res_date.day}일"
                        metric = metric_names.get(res["metric"], res["metric"])
                        direction = "증가" if res.get("is_higher") else "감소"
                        anomaly_summary += f"- {dt_kor}: {metric} 수치가 평소보다 {direction}했다멍! "

        # 2) daily / weekly 프롬프트 구성
        if mode == "daily":
            sleep_fmt = self.format_time(metrics.get("sleep_min", 0))
            screen_fmt = self.format_time(metrics.get("screen_min", 0))
            apps_str = ", ".join(metrics.get("top_3_apps", [])) if metrics.get("top_3_apps") else "없음"

            # ✅ Processor가 넣어준 brief
            events_brief = metrics.get("today_events_brief", "오늘 일정 없음")
            weather_brief = metrics.get("today_weather_brief", "오늘 날씨 데이터 없음")

            guide = f"""
[분석 대상 날짜] {display_date}
[오늘의 지표]
- 걸음수: {metrics.get('steps', 0)}보, 수면: {sleep_fmt}({metrics.get('sleep_start_hour')}시 취침), 폰: {screen_fmt}(앱: {apps_str}), 지출: {metrics.get('total_spending', 0)}원
[오늘 일정] {events_brief}
[오늘 날씨] {weather_brief}
[특이사항] {anomaly_summary}
"""
            task = f"""{display_date}의 지표와 평소 패턴 대비 특이점을 분석해서 리포트를 써줘.
절대 날짜(예: 10월 1일)를 시간(10시 1분)으로 해석하면 안 돼멍.
오늘의 핵심을 4문장 이내로, 걸음/수면/폰/지출을 한 번씩 언급하면서 요약하고,
추가로 '오늘 일정'과 '오늘 날씨'도 각각 한 번씩 자연스럽게 언급해줘멍!
저조한 데이터에 대해서는 행동 제안 1개만 딱 찝어줘멍!"""
            system_content = f"너는 주인님의 {display_date} 하루를 챙기는 밀착 관리 강아지야."
            time_word = "오늘"

        else:
            avg_sleep_fmt = self.format_time(int(metrics.get("avg_sleep_min", 0)))
            avg_screen_fmt = self.format_time(int(metrics.get("avg_screen_min", 0)))

            days = self._calc_days_from_period(metrics.get("period"))
            avg_daily_billing = int((metrics.get("total_spending", 0) or 0) / max(days, 1))

            max_bill = metrics.get("max_spending", {"amount": 0, "date": "없음"})
            min_bill = metrics.get("min_spending", {"amount": 0, "date": "없음"})

            weekly_events_brief = metrics.get("weekly_calendar_brief", "이번 주 일정 없음")
            weekly_weather_brief = metrics.get("weekly_weather_brief", "이번 주 날씨 데이터 없음")

            max_day_eval = "평균보다 많이 쓴 과소비 날"
            min_day_eval = "평균보다 적게 쓴 절약한 날"

            guide = f"""
[주간 기준 데이터]
- 하루 평균 지출액: {avg_daily_billing:,}원
- 가장 많이 쓴 날({max_day_eval}): {max_bill.get('date')} ({int(max_bill.get('amount', 0)):,}원)
- 가장 적게 쓴 날({min_day_eval}): {min_bill.get('date')} ({int(min_bill.get('amount', 0)):,}원)

[일주일 평균 데이터]
- 평균 걸음: {metrics.get('avg_steps', 0)}보, 수면: {avg_sleep_fmt}, 폰사용: {avg_screen_fmt} (가장 많이 쓴 앱: {metrics.get('most_used_app', '없음')})
- 총 지출: {int(metrics.get('total_spending', 0)):,}원

[이번 주 일정] {weekly_events_brief}
[이번 주 날씨] {weekly_weather_brief}

[일주일 중 유독 특별했던 순간들]
{anomaly_summary if anomaly_summary else "이번 주는 큰 기복 없이 평온했다멍!"}
"""
            task = f"""
1. 일주일 분석을 4문장 이내로 간략하게
2. 지난 일주일 동안의 전체적인 생활 패턴(건강, 절약, 폰 사용)을 종합적으로 평가해줘.
3. 지출 분석 시 {max_bill.get('date')}은 무조건 '평균보다 많이 쓴 날'로, {min_bill.get('date')}은 '적게 쓴 날'로 명확히 구분해서 말해줘멍.
4. 특히 {max_bill.get('date')}에 지출한 {int(max_bill.get('amount', 0)):,}원은 하루 평균({avg_daily_billing:,}원)보다 훨씬 큰 금액임을 강조하며 혼내줘멍.
5. 가장 부족한 부분에 대해 다음 주 개선 행동을 제안해줘멍!
6. 추가로 '이번 주 일정'과 '이번 주 날씨'도 각각 한 번씩 언급해줘멍!
"""
            system_content = "너는 주인님의 '한 주 패턴'을 분석하는 전략가 강아지야. 모든 분석은 '일주일 평균'과 '흐름' 기준이야."
            time_word = "이번 주"

        # 3) 최종 LLM 프롬프트
        prompt = f"""
[절대 규칙: 전체 답변을 4문장 이내로 아주 짧게 작성할것. 반드시 한국어로만 답변하십시오. 중국어나 한자를 절대 섞지 마십시오.]
너는 완벽한 한국어를 구사하는 라이프로그 분석 강아지 '하루'야.
정보: {guide}
지시: {task}

[규칙]
1. 정보에 적힌 '실제값' 숫자를 절대 수정하거나 멋대로 계산하지 마십시오. (1원 단위까지 정확히 쓸 것)
2. 특이사항에 '많음(Over)'이라 적혀있으면 반드시 평소보다 많이 했다고 말하십시오.
3. 반드시 '{time_word}'이라는 시점에 맞춰서 이야기해줘.
4. 날짜(예: 10월 1일)를 보고 절대 시간(10시 1분)으로 말하지 마. 날짜는 날짜일 뿐이야!
5. 수치 나열보다는 '패턴'을 해석해줘.
6. 말투는 반드시 '~멍!', '~했다멍!'으로 끝나야 해.
7. 시간은 무조건 'X시간 X분' 형식으로 말하고 '분'으로만 말하지 마.
8. 결과보다는 앞으로의 변화(행동 제안)에 초점을 맞춰줘멍!
9. 이상치가 있는 날은 반드시 '이번 주 평균' 수치와 직접 비교해서 얼마나 더 많이/적게 했는지 구체적으로 강조해줘멍!
10. 중국어/일본어/영어 절대 금지. 오직 한국어만 사용해라멍!
11. daily면 '오늘 일정'과 '오늘 날씨', weekly면 '이번 주 일정'과 '이번 주 날씨'를 각각 한 번씩 꼭 언급해라멍!
"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": system_content
                    + " 한국어만 사용하며 중국어는 절대 사용하지 마세요. 시간은 항상 '시간/분'으로 변환해서 말해줘.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.4,
        )
        return response.choices[0].message.content.strip()

    # -------------------------
    # Daily quests
    # -------------------------
    def generate_daily_quests(self, daily_data: Dict[str, Any], anomaly_results: Optional[List[Dict[str, Any]]]) -> str:
        metrics = daily_data["metrics"]
        status = daily_data["status"]

        anomaly_targets: List[str] = []
        if status.get("step_eval") == "잔소리":
            anomaly_targets.append("걸음수 증진")
        if status.get("sleep_eval") in ["잔소리", "너무많음"]:
            anomaly_targets.append("수면 패턴 개선")
        if status.get("spending_eval") == "과소비":
            anomaly_targets.append("지출 절제")
        if status.get("screen_eval") == "잔소리":
            anomaly_targets.append("스크린타임 감축")

        if anomaly_results:
            for res in anomaly_results:
                if abs(res.get("z_score", 0)) > 1.5:
                    mapping = {"steps": "걸음수 증진", "screen": "스크린타임 감축", "sleep": "수면 패턴 개선", "billing": "지출 절제"}
                    t_name = mapping.get(res.get("metric"))
                    if t_name and t_name not in anomaly_targets:
                        anomaly_targets.append(t_name)

        num_quests = random.choice([1, 2])
        quest1_cat = random.choice(anomaly_targets) if anomaly_targets else "건강 유지 활동"
        quest2_cat = None
        if num_quests == 2:
            all_cats = ["걸음수 증진", "수면 패턴 개선", "지출 절제", "스크린타임 감축"]
            quest2_cat = random.choice([c for c in all_cats if c != quest1_cat])

        sleep_fmt = self.format_time(metrics.get("sleep_min", 0))
        screen_fmt = self.format_time(metrics.get("screen_min", 0))
        top_app = (metrics.get("top_3_apps") or ["앱"])[0]

        if num_quests == 1:
            target_info = f"퀘스트 1 (집중 관리): {quest1_cat}"
            output_example = """퀘스트 1: (미션 내용)
난이도: (이지/노멀/하드)
리워드: (숫자)

한마디: (응원 멘트)"""
        else:
            target_info = f"퀘스트 1 (집중 관리): {quest1_cat}\n퀘스트 2 (균형 관리): {quest2_cat}"
            output_example = """퀘스트 1: (미션 내용)
난이도: (이지/노멀/하드)
리워드: (숫자)

퀘스트 2: (미션 내용)
난이도: (이지/노멀/하드)
리워드: (숫자)

한마디: (응원 멘트)"""

        prompt = f"""
[지시] 너는 퀘스트 마스터 강아지 '하루'야. 주인님께 {num_quests}개의 일일 퀘스트를 작성하라멍!
각 퀘스트는 데이터에 기반하여 구체적인 수치와 행동을 포함해야 한다멍.

[건강 가이드라인 - 이 범위를 지켜라멍!]
- 스크린타임: "몇 시까지"가 아니라 "오늘 총 사용 시간 X시간 X분 이내로 제한하기" 또는 "어제보다 X분 줄이기"로 제안해멍.
- 특정 앱: "가장 많이 쓴 앱({top_app}) 사용 시간을 X분 이내로 줄이기"처럼 구체적으로 말해멍.
- 수면: 7시간 ~ 8시간이 가장 건강하다멍. 9시간 이상은 '과잉 수면'이니 줄이라고 말해줘멍.
- 걸음: 8,000보 ~ 10,000보가 적당하다멍. 이미 달성했다면 '유지'나 '근력 운동'으로 유도해멍.
- 지출: 어제 많이 썼다면 오늘은 '무지출'이나 '소액 지출'을 권장해멍.

[리워드 지급 기준 - 반드시 준수]
- 이지: 10 ~ 50
- 노멀: 60 ~ 100
- 하드: 100 ~ 150

[미션 주제]
{target_info}

[데이터]
걸음: {metrics.get('steps', 0)}보, 수면: {sleep_fmt}, 폰사용: {screen_fmt}, 지출: {metrics.get('total_spending', 0)}원

[출력 양식 - 이대로만 출력해!]
{output_example}

[절대 규칙]
1. '리워드'는 **숫자만** 써라멍.
2. 시간은 반드시 'X시간 X분'으로만 말해라멍.
3. 중국어/일본어/영어 절대 금지. 오직 한국어만 써라멍!
4. 말투는 반드시 '~멍!'으로 끝내라멍.
5. 미션 내용은 반드시 구체적이어야 한다멍.
6. 물리적 모순 금지.
"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "너는 불필요한 설명을 생략하고 지정된 양식만 한국어로 출력하는 로봇 강아지야."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=250,
        )
        return response.choices[0].message.content.strip()

    # -------------------------
    # Weekly quest
    # -------------------------
    def generate_weekly_quest(self, weekly_data: Dict[str, Any]) -> str:
        metrics = weekly_data

        avg_sleep_fmt = self.format_time(int(metrics.get("avg_sleep_min", 0)))
        avg_screen_fmt = self.format_time(int(metrics.get("avg_screen_min", 0)))

        prompt = f"""
너는 주인님의 라이프 스타일을 업그레이드해주는 '전략가 강아지 하루'야.
지난주 데이터를 바탕으로 이번 주 일주일 동안 달성할 '통합 주간 퀘스트'를 하나 생성해줘멍!

[지난주 데이터 요약]
- 평균 걸음: {metrics.get('avg_steps', 0)}보
- 평균 수면: {avg_sleep_fmt}
- 평균 스마트폰 사용 시간: {avg_screen_fmt} (가장 많이 쓴 앱: {metrics.get('most_used_app', '없음')})
- 총 지출: {int(metrics.get('total_spending', 0)):,}원

[출력 양식 - 이대로만 출력해!]
주간 퀘스트: (구체적 목표 수치와 실천 방법이 포함된 미션 내용)
난이도: (이지/노멀/하드)
리워드: (300 ~ 1000 사이 숫자만)
한마디: (장기 도전을 응원하는 듬직한 한마디)

[절대 규칙]
1. 리워드는 300 ~ 1000 사이의 숫자만 써라멍.
2. 시간은 반드시 'X시간 X분' 형식으로 말해라멍.
3. 지난주 데이터보다 약 10%~20% 정도 도전적인 목표를 포함해라멍.
4. 말투는 반드시 '~멍!'으로 끝나야 한다멍. 한국어만 사용해라멍.
"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "너는 주인님의 데이터를 분석해 성장을 돕는 친절한 강아지야."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.5,
        )
        return response.choices[0].message.content.strip()
