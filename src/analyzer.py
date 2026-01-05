import pandas as pd
import numpy as np
from statsmodels.tsa.seasonal import STL

class LifeLogAnalyzer:
    def __init__(self, steps_path, sleep_path, screen_path, billing_path):
        # 1. 데이터 로드 및 전처리 (날짜 기준 집계)
        self.df_steps = self._prepare_data(pd.read_csv(steps_path), 'date', 'total_steps')
        self.df_sleep = self._prepare_data(pd.read_csv(sleep_path), 'date', 'duration_min')
        
        # 스크린타임은 ms 단위를 분(min) 단위로 변환
        screen_df = pd.read_csv(screen_path)
        screen_df['total_min'] = screen_df['totalTimeInForeground_ms'] / (1000 * 60)
        self.df_screen = self._prepare_data(screen_df, 'date', 'total_min')
        
        # 지출 데이터 전처리
        billing_df = pd.read_csv(billing_path)
        billing_df['date'] = billing_df['timestamp'].str[:10]
        self.df_billing = self._prepare_data(billing_df, 'date', 'amount_krw')

    def _prepare_data(self, df, date_col, value_col):
        """날짜별로 합산하고 시계열 빈도를 맞춤 (빈 날짜는 0 채움)"""
        df[date_col] = pd.to_datetime(df[date_col])
        series = df.groupby(date_col)[value_col].sum().asfreq('D').fillna(0)
        return series

    def analyze_anomaly(self, metric_type, target_date):
        """
        특정 지표와 날짜에 대해 STL 이상치 분석 수행
        metric_type: 'steps', 'sleep', 'screen', 'billing'
        """
        # 분석 대상 선택
        series_map = {
            'steps': self.df_steps,
            'sleep': self.df_sleep,
            'screen': self.df_screen,
            'billing': self.df_billing
        }
        series = series_map.get(metric_type)
        
        if series is None or len(series) < 14: # 최소 2주 데이터 필요
            return {"is_anomaly": False, "reason": "데이터 부족"}

        # 1. STL 분해 (주기 7일)
        stl = STL(series, period=7, robust=True)
        result = stl.fit()
        
        # 2. 잔차(Residual) 기반 Z-Score 계산
        resid = result.resid
        mu = resid.mean()
        sigma = resid.std()
        
        # 3. 대상 날짜의 수치 추출
        target_dt = pd.to_datetime(target_date)
        if target_dt not in resid.index:
            return {"is_anomaly": False, "reason": "해당 날짜 데이터 없음"}
            
        z_score = (resid[target_dt] - mu) / (sigma if sigma != 0 else 1)
        
        # 4. 이상치 판정 (Z-Score 2.5 기준)
        is_anomaly = abs(z_score) > 2.5
        
        return {
            "date": target_date,
            "metric": metric_type,
            "actual_value": series[target_dt],
            "z_score": round(z_score, 2),
            "is_anomaly": is_anomaly,
            "trend": round(result.trend[target_dt], 2),
            "is_higher": z_score > 0  # 평소보다 높은지 낮은지
        }
