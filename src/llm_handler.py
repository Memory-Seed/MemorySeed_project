from openai import OpenAI
import pandas as pd

class QwenAnalyst:
    def __init__(self):
        self.client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
        self.model = "qwen2.5:7b"

    def format_time(self, minutes):
        """분을 'X시간 X분' 형식으로 변환"""
        if minutes < 0: minutes = abs(minutes)
        if minutes < 60: return f"{minutes}분"
        h = minutes // 60
        mins = minutes % 60
        return f"{h}시간 {mins}분"

    def analyze(self, data, anomaly_results=None):
        mode = data['type']
        metrics = data['metrics'] # 지표 데이터

        # 0. 날짜 가공 (데이터에 날짜 정보가 있다면 'X월 X일' 형태로 변환)
        raw_date = data.get('date', '')
        if raw_date:
            try:
                date_obj = pd.to_datetime(raw_date)
                display_date = f"{date_obj.month}월 {date_obj.day}일"
            except:
                display_date = raw_date
        else:
            display_date = "오늘"
        
        # 1. STL 이상치 정리
        anomaly_summary = ""
        if anomaly_results:
            metric_names = {
                "steps": "걸음수",
                "sleep": "수면 시간",
                "screen": "폰 사용 시간",
                "billing": "지출 금액"
            }
            
            # 주간 모드일 때는 이번 주 평균값과 직접 비교하는 문구 생성
            if mode == "weekly":
                # 주간 평균/기준 데이터 매핑
                avg_spending_per_day = metrics.get('total_spending', 0) / 7
                avg_ref = {
                    "steps": metrics.get('avg_steps', 0),
                    "sleep": metrics.get('avg_sleep_min', 0),
                    "screen": metrics.get('avg_screen_min', 0),
                    "billing": avg_spending_per_day
                }
                
                for res in anomaly_results:
                    if res.get('is_anomaly'):
                        res_date = pd.to_datetime(res['date'])
                        dt_kor = f"{res_date.month}월 {res_date.day}일"
                        
                        m_key = res['metric']
                        m_label = metric_names.get(m_key, m_key)
                        actual = res['actual_value']
                        avg_val = avg_ref.get(m_key, 0)
                        diff = abs(actual - avg_val)
                        
                        # 단위 및 포맷 설정
                        if m_key == "steps":
                            act_s, avg_s, diff_s = f"{int(actual)}보", f"{int(avg_val)}보", f"{int(diff)}보"
                        elif m_key in ["sleep", "screen"]:
                            act_s, avg_s, diff_s = self.format_time(int(actual)), self.format_time(int(avg_val)), self.format_time(int(diff))
                        else: # billing
                            act_s, avg_s, diff_s = f"{int(actual)}원", f"{int(avg_val)}원", f"{int(diff)}원"
                            
                        direction = "많음(Over)" if res['is_higher'] else "적음(Under)"
                        anomaly_summary += f"- {dt_kor}: {m_label}가 {act_s}로, 이번 주 평균({avg_s})보다 {diff_s}이나 더 {direction}! "
            
            else: # daily 모드
                for res in anomaly_results:
                    if res.get('is_anomaly'):
                        res_date = pd.to_datetime(res['date'])
                        dt_kor = f"{res_date.month}월 {res_date.day}일"
                        metric = metric_names.get(res['metric'], res['metric'])
                        direction = "증가" if res['is_higher'] else "감소"
                        anomaly_summary += f"- {dt_kor}: {metric} 수치가 평소보다 {direction}했다멍! "

        if mode == "daily":
            s = data['status']
            sleep_fmt = self.format_time(metrics['sleep_min'])
            screen_fmt = self.format_time(metrics['screen_min'])
            apps_str = ", ".join(metrics['top_3_apps'])
            
            guide = f"""
            [분석 대상 날짜] {display_date}
            [오늘의 지표]
            - 걸음수: {metrics['steps']}보, 수면: {sleep_fmt}({metrics['sleep_start_hour']}시 취침), 폰: {screen_fmt}(앱: {apps_str}), 지출: {metrics['total_spending']}원
            [특이사항] {anomaly_summary}
            """
            task = f"{display_date}의 지표와 평소 패턴 대비 특이점을 분석해서 리포트를 써줘. 절대 날짜(예: 10월 1일)를 시간(10시 1분)으로 해석하면 안 돼멍 그리고 오늘의 핵심을 3문장 내외로 모든 지표(걸음, 수면, 폰, 지출)를 한 번씩 언급하면서 요약해서 칭찬이나 잔소리를 해줘. 저조한 데이터에대해서는 행동 제안 1개만 딱 찝어줘멍!"
            system_content = f"너는 주인님의 {display_date} 하루를 챙기는 밀착 관리 강아지야."
            time_word = "오늘"

        else: # weekly
            avg_sleep_fmt = self.format_time(int(metrics['avg_sleep_min']))
            avg_screen_fmt = self.format_time(int(metrics['avg_screen_min']))
            avg_daily_billing = int(metrics.get('total_spending', 0) / 7)
    
            max_bill = metrics['max_spending']
            min_bill = metrics['min_spending']

            # 중요: LLM이 계산하게 두지 말고, 여기서 결론(많음/적음)을 미리 정해줍니다.
            max_day_eval = "평균보다 많이 쓴 과소비 날" 
            min_day_eval = "평균보다 적게 쓴 절약한 날"

            guide = f"""
            [주간 기준 데이터]
            - 하루 평균 지출액: {avg_daily_billing:,}원
            - 가장 많이 쓴 날({max_day_eval}): {max_bill['date']} ({max_bill['amount']:,}원)
            - 가장 적게 쓴 날({min_day_eval}): {min_bill['date']} ({min_bill['amount']:,}원)

            [일주일 평균 데이터]
            - 평균 걸음: {metrics['avg_steps']}보, 수면: {avg_sleep_fmt}, 폰사용: {avg_screen_fmt} 가장 많이 쓴 앱: {metrics['most_used_app']})
            - 일주일 총 지출: {metrics['total_spending']:,}원
            
            [일주일 중 유독 특별했던 순간들]
            {anomaly_summary if anomaly_summary else "이번 주는 큰 기복 없이 평온했다멍!"}
            """
            task = """
            1. 일주일 분석을 4줄이내로 간략하게 
            2. 지난 일주일 동안의 전체적인 생활 패턴(건강, 절약, 폰 사용)을 종합적으로 평가해줘.
            3. 지출 분석 시 {max_bill['date']}은 무조건 '평균보다 많이 쓴 날'로, {min_bill['date']}은 '적게 쓴 날'로 명확히 구분해서 말해줘멍.
            4. 특히 {max_bill['date']}에 지출한 {max_bill['amount']:,}원은 하루 평균({avg_daily_billing:,}원)보다 훨씬 큰 금액임을 강조하며 혼내줘멍.
            5. 가장 부족한 부분에 대해 다음 주 개선 행동을 제안해줘멍!
            """
            system_content = "너는 주인님의 '한 주 패턴'을 분석하는 전략가 강아지야. 모든 분석은 '일주일 평균'과 '흐름' 기준이야."
            time_word = "이번 주"

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
        5. 수치 나열보다는 "이번 주는 평소보다 잠이 부족한 편이었다멍" 처럼 '패턴'을 해석해줘.
        6. 말투는 반드시 '~멍!', '~했다멍!'으로 끝나야 해.
        7. 시간은 무조건 'X시간 X분' 형식으로 말하고 '분'으로만 말하지 마.
        8. 결과보다는 앞으로의 변화(행동 제안)에 초점을 맞춰줘멍!
        9. 추가 규칙: 이상치가 있는 날(특별했던 순간들)에 대해서는 반드시 정보에 적힌 '이번 주 평균' 수치와 직접 비교해서 얼마나 더 많이/적게 했는지 구체적으로 강조해서 말해줘멍!
        10. 언어 규칙: 중국어나 외국어를 사용하면 나쁜 강아지다멍. 오직 한국어만 사용해서 정답을 말해줘멍!
        """
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_content + " 한국어만 사용하며 중국어는 절대 사용하지 마세요. 시간은 항상 '시간/분'으로 변환해서 말해줘."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4
        )
        return response.choices[0].message.content
    

    