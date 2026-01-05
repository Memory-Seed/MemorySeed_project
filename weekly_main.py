from src.processor import DataProcessor
from src.llm_handler import QwenAnalyst
from src.analyzer import LifeLogAnalyzer
import pandas as pd

def run_weekly_analysis():
    # 1. 모듈 초기화
    processor = DataProcessor()
    analyst = QwenAnalyst()
    life_analyzer = LifeLogAnalyzer(
        'data/steps.csv', 
        'data/sleep.csv', 
        'data/screentime.csv', 
        'data/notification.csv'
    )

    # 분석하고 싶은 주간 범위 설정
    start_dt, end_dt = "2025-09-13", "2025-09-19"
    
    # 2. 주간 데이터 요약 집계 (평균치 등)
    weekly_res = processor.get_weekly_summary(start_dt, end_dt)
    
    # 3. 해당 주간 내에 발생한 '이상치(특별한 날)'들 수집
    # 주간 범위 내 모든 날짜를 리스트로 만듭니다.
    date_range = pd.date_range(start=start_dt, end=end_dt).strftime('%Y-%m-%d')
    
    all_weekly_anomalies = []
    metrics_to_check = ['steps', 'sleep', 'screen', 'billing']
    
    for target_date in date_range:
        for metric in metrics_to_check:
            res = life_analyzer.analyze_anomaly(metric, target_date)
            if res.get('is_anomaly'):
                all_weekly_anomalies.append(res)
    
    # 4. LLM 전송용 페이로드 구성
    weekly_payload = {
        "type": "weekly",
        "metrics": weekly_res
    }

    print(f"\n[📅 {start_dt} ~ {end_dt} 주간 종합 리포트다멍!]")
    print("=" * 60)
    
    # 5. LLM 분석 요청 (주간 요약 데이터 + 주간 이상치 리스트 전달)
    report = analyst.analyze(weekly_payload, all_weekly_anomalies)
    print(report)
    print("=" * 60)

if __name__ == "__main__":
    run_weekly_analysis()