import pandas as pd

class DataProcessor:
    def __init__(self):
        self.steps = pd.read_csv('data/steps.csv')
        self.sleep = pd.read_csv('data/sleep.csv')
        self.billing = pd.read_csv('data/notification.csv')
        self.screen = pd.read_csv('data/screentime.csv')

    def get_daily_data(self, target_date):
        # 1. 걸음수 및 수면 (기존 로직)
        step_val = self.steps[self.steps['date'] == target_date]['total_steps'].sum()
        sleep_row = self.sleep[self.sleep['date'] == target_date]
        sleep_min = sleep_row['duration_min'].sum()
        start_hour = int(sleep_row.iloc[0]['sleep_start_time'].split(' ')[1].split(':')[0]) if not sleep_row.empty else None

        # 2. 스크린타임 및 TOP 3 앱 추출
        day_screen = self.screen[self.screen['date'] == target_date]
        screen_min = day_screen['totalTimeInForeground_ms'].sum() / (1000 * 60)
        
        # 앱별로 사용량 합계 내서 상위 3개 뽑기
        top_apps_list = (day_screen.groupby('packageName')['totalTimeInForeground_ms']
                         .sum().sort_values(ascending=False).head(3))
        # 패키지명 마지막 단어만 추출 (예: com.instagram.android -> instagram)
        top_3_apps = [app.split('.')[-1] for app in top_apps_list.index.tolist()]

        # 3. 결제 내역 (기존 로직)
        day_bills = self.billing[self.billing['timestamp'].str.contains(target_date)]
        total_spending = day_bills['amount_krw'].sum()
        late_spending = any(int(t.split(' ')[1].split(':')[0]) >= 22 for t in day_bills['timestamp'])

        return {
            "type": "daily",
            "date": target_date,
            "metrics": {
                "steps": int(step_val),
                "sleep_min": int(sleep_min),
                "sleep_start_hour": start_hour,
                "screen_min": int(screen_min),
                "top_3_apps": top_3_apps,
                "total_spending": int(total_spending)
            },
            "status": {
                "step_eval": "칭찬" if step_val >= 8000 else ("잔소리" if step_val < 4000 else "보통"),
                "sleep_eval": "칭찬" if 420 <= sleep_min < 540 else ("너무많음" if sleep_min >= 540 else ("잔소리" if sleep_min <= 300 else "보통")),
                "sleep_start_eval": "늦게잠" if start_hour is not None and (1 <= start_hour < 5) else "일찍잠",
                "screen_eval": "칭찬" if screen_min <= 120 else ("잔소리" if screen_min >= 240 else "보통"),
                "spending_eval": "과소비" if total_spending >= 100000 else ("절약왕" if total_spending == 0 else "보통"),
                "late_night_snack": late_spending
            }
        }

    def get_weekly_summary(self, start_date, end_date):
        mask = (self.steps['date'] >= start_date) & (self.steps['date'] <= end_date)
        avg_steps = self.steps[mask]['total_steps'].mean()
        avg_sleep = self.sleep[(self.sleep['date'] >= start_date) & (self.sleep['date'] <= end_date)]['duration_min'].mean()
        total_spending = self.billing[self.billing['timestamp'].str[:10].between(start_date, end_date)]['amount_krw'].sum()
        
        # 주간 가장 많이 사용한 앱 1위
        week_screen = self.screen[(self.screen['date'] >= start_date) & (self.screen['date'] <= end_date)]
        most_used_app = week_screen.groupby('packageName')['totalTimeInForeground_ms'].sum().idxmax().split('.')[-1] if not week_screen.empty else "없음"
        avg_screen = week_screen.groupby('date')['totalTimeInForeground_ms'].sum().mean() / (1000 * 60)

        # 1. 주간 지출 데이터 필터링
        weekly_bills = self.billing[self.billing['timestamp'].str[:10].between(start_date, end_date)].copy()
        weekly_bills['date'] = weekly_bills['timestamp'].str[:10]
        
        # 날짜별 합계 계산
        daily_spending = weekly_bills.groupby('date')['amount_krw'].sum()
        
        # 지출 최대/최소 날짜 및 금액 추출
        max_spend_val = daily_spending.max() if not daily_spending.empty else 0
        max_spend_date = daily_spending.idxmax() if not daily_spending.empty else "없음"
        min_spend_val = daily_spending.min() if not daily_spending.empty else 0
        min_spend_date = daily_spending.idxmin() if not daily_spending.empty else "없음"

        return {
            "type": "weekly",
            "period": f"{start_date} ~ {end_date}",
            "avg_steps": round(avg_steps, 1),
            "avg_sleep_min": round(avg_sleep, 1),
            "avg_screen_min": int(avg_screen),
            "most_used_app": most_used_app,
            "total_spending": int(total_spending),
            # 지출 분석용 데이터 추가
            "max_spending": {"amount": int(max_spend_val), "date": max_spend_date},
            "min_spending": {"amount": int(min_spend_val), "date": min_spend_date},
            "most_used_app": most_used_app
        }