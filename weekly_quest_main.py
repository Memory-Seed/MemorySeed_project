from src.processor import DataProcessor
from src.llm_handler import QwenAnalyst


def main():

    processor = DataProcessor(
        steps_path="data/steps.json",
        sleep_path="data/sleep.json",
        billing_path="data/notification.json",
        screen_path="data/screentime.json",
        calendar_path="data/google_calendar.json",
        weather_path="data/accuweather.json",
    )

    analyst = QwenAnalyst()

    # 지난주 분석 범위
    data_start = "2026-01-05"
    data_end = "2026-01-11"

    # 이번주 표시용
    quest_period = "2026-01-12 ~ 2026-01-18"

    print(f"\n[📊 {data_start} ~ {data_end} 기록 분석 중...]")

    # 1. 지난주 데이터 집계
    weekly_res = processor.get_weekly_summary(data_start, data_end)

    if not weekly_res:
        print("분석할 데이터가 부족하다멍!")
        return

    # 2. 주간 퀘스트 생성
    weekly_quest = analyst.generate_weekly_quest(weekly_res)

    # 3. 출력
    print(f"\n[🏆 이번 주 주간 미션 ({quest_period})]")
    print("=" * 60)
    print(weekly_quest)
    print("=" * 60)
    print(f"🐾 지난주({data_start}~{data_end})보다 더 발전한 모습을 기대한다멍!")


if __name__ == "__main__":
    main()
