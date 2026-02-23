from src.processor import DataProcessor
from src.llm_handler import QwenAnalyst
from src.analyzer import LifeLogAnalyzer


def main():
    # ✅ JSON + (선택) calendar/weather 포함
    processor = DataProcessor(
        steps_path="data/steps.json",
        sleep_path="data/sleep.json",
        billing_path="data/notification.json",
        screen_path="data/screentime.json",
        calendar_path="data/google_calendar.json",
        weather_path="data/accuweather.json",
    )

    analyst = QwenAnalyst()

    # ✅ STL 이상치 분석기: CSV → JSON
    life_analyzer = LifeLogAnalyzer(
        "data/steps.json",
        "data/sleep.json",
        "data/screentime.json",
        "data/notification.json",
    )

    # [테스트 설정] 어제의 데이터를 분석합니다.
    yesterday = "2026-01-11"
    # [시연 설정] 오늘 날짜를 표시합니다.
    today = "2026-01-12"

    print(f"\n[📊 분석 날짜: {yesterday} (어제)]")

    # 1) 어제 하루치 데이터 수집
    daily_res = processor.get_daily_data(yesterday)

    # 2) 어제 데이터가 평소 패턴 대비 이상했는지 분석
    anomalies = []
    for m in ["steps", "sleep", "screen", "billing"]:
        res = life_analyzer.analyze_anomaly(m, yesterday)
        if res.get("is_anomaly"):
            anomalies.append(res)

    print(f"\n[🦴 {today} 오늘의 하루 미션!]")
    print("=" * 60)

    # 3) 퀘스트 생성 (어제의 부족함을 채우는 오늘의 미션)
    quests = analyst.generate_daily_quests(daily_res, anomalies)
    print(quests)

    print("=" * 60)


if __name__ == "__main__":
    main()
