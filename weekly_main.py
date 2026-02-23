from src.processor import DataProcessor
from src.llm_handler import QwenAnalyst
from src.analyzer import LifeLogAnalyzer
import pandas as pd


def run_weekly_analysis():
    # 1) 모듈 초기화 (JSON + calendar/weather 포함)
    processor = DataProcessor(
        steps_path="data/steps.json",
        sleep_path="data/sleep.json",
        billing_path="data/notification.json",
        screen_path="data/screentime.json",
        calendar_path="data/google_calendar.json",
        weather_path="data/accuweather.json",
    )

    analyst = QwenAnalyst()

    # 2) 이상치 분석기 (JSON 기반)
    life_analyzer = LifeLogAnalyzer(
        "data/steps.json",
        "data/sleep.json",
        "data/screentime.json",
        "data/notification.json",
    )

    # 분석하고 싶은 주간 범위 설정
    start_dt, end_dt = "2026-01-12", "2026-01-18"

    # 3) 주간 데이터 요약 집계 (평균치 등)  ✅ 함수명 유지
    weekly_res = processor.get_weekly_summary(start_dt, end_dt)

    # 4) 주간 내 '이상치(특별한 날)' 수집
    date_range = pd.date_range(start=start_dt, end=end_dt).strftime("%Y-%m-%d")

    all_weekly_anomalies = []
    metrics_to_check = ["steps", "sleep", "screen", "billing"]

    for target_date in date_range:
        for metric in metrics_to_check:
            res = life_analyzer.analyze_anomaly(metric, target_date)
            if res.get("is_anomaly"):
                all_weekly_anomalies.append(res)

    # 5) LLM 전송용 페이로드 구성
    weekly_payload = {
        "type": "weekly",
        "metrics": weekly_res,  # weekly_res 안에 weekly_calendar_brief / weekly_weather_brief 포함됨
    }

    print(f"\n[📅 {start_dt} ~ {end_dt} 주간 종합 리포트다멍!]")
    print("=" * 60)

    # 6) LLM 분석 요청 (주간 요약 + 이상치 리스트)
    report = analyst.analyze(weekly_payload, all_weekly_anomalies)
    print(report)

    print("=" * 60)


if __name__ == "__main__":
    run_weekly_analysis()
