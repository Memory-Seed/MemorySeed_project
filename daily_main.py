from src.processor import DataProcessor
from src.llm_handler import QwenAnalyst
from src.analyzer import LifeLogAnalyzer


def run_daily_analysis():

    # 1. 데이터 로더 (JSON 기반)
    processor = DataProcessor(
        steps_path="data/steps.json",
        sleep_path="data/sleep.json",
        billing_path="data/notification.json",
        screen_path="data/screentime.json",
        calendar_path="data/google_calendar.json",
        weather_path="data/accuweather.json"
    )

    # 2. LLM 분석기
    analyst = QwenAnalyst()

    # 3. 이상치 분석기 (JSON 기반)
    life_analyzer = LifeLogAnalyzer(
        'data/steps.json',
        'data/sleep.json',
        'data/screentime.json',
        'data/notification.json'
    )

    # 분석 날짜
    target_date = "2026-01-12"

    # 4. 일일 데이터 수집
    daily_res = processor.get_daily_data(target_date)

    # 5. STL 이상치 분석
    metrics_to_check = ['steps', 'sleep', 'screen', 'billing']
    anomaly_results = []

    for metric in metrics_to_check:
        res = life_analyzer.analyze_anomaly(metric, target_date)
        if res.get('is_anomaly'):
            anomaly_results.append(res)

    # 6. 출력
    print(f"\n[🐾 {target_date} 오늘의 하루 리포트다멍!]")
    print("-" * 50)

    report = analyst.analyze(daily_res, anomaly_results)

    print(report)
    print("-" * 50)


if __name__ == "__main__":
    run_daily_analysis()
