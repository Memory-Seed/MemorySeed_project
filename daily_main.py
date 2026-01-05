from src.processor import DataProcessor
from src.llm_handler import QwenAnalyst
from src.analyzer import LifeLogAnalyzer  # STL 분석기 임포트

def run_daily_analysis():
    # 1. 각 모듈 초기화
    processor = DataProcessor()
    analyst = QwenAnalyst()
    # 파일 경로들을 인자로 넣어 analyzer 생성
    life_analyzer = LifeLogAnalyzer(
        'data/steps.csv', 
        'data/sleep.csv', 
        'data/screentime.csv', 
        'data/notification.csv'
    )

    # 분석하고 싶은 날짜 설정
    target_date = "2025-10-01" # 예시 데이터가 풍부한 날짜로 설정
    
    # 2. 기존 방식: 일간 데이터 수집 및 상태 판별 (절대적 수치)
    daily_res = processor.get_daily_data(target_date)
    
    # 3. STL 방식: 통계적 이상치 탐지 (상대적 수치)
    # 주요 지표 4개에 대해 이상치가 있는지 리스트로 수집합니다.
    metrics_to_check = ['steps', 'sleep', 'screen', 'billing']
    anomaly_results = []
    
    for metric in metrics_to_check:
        res = life_analyzer.analyze_anomaly(metric, target_date)
        # 이상치로 판명된 경우에만 리스트에 담아 LLM에게 전달
        if res.get('is_anomaly'):
            anomaly_results.append(res)
    
    print(f"\n[🐾 {target_date} 오늘의 하루 리포트다멍!]")
    print("-" * 50)
    
    # 4. LLM 분석 요청 (기존 데이터 + 이상치 결과 함께 전달)
    # 수정하신 llm_handler의 analyze 함수는 anomaly_results를 두 번째 인자로 받습니다.
    report = analyst.analyze(daily_res, anomaly_results)
    
    print(report)
    print("-" * 50)

if __name__ == "__main__":
    run_daily_analysis()