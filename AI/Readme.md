
# CD_HARU — LifeLog 분석 파이프라인

## 디렉토리 구조

```
CD_HARU/
├── run_weekly_llm_report.py       # Step 1: 전처리 실행 파일
├── run_llm_analysis_with_score.py # Step 2: LLM 분석 + 점수 계산 실행 파일
│
├── data/
│   ├── raw/                       # 원본 데이터 (CSV, JSON)
│   │   ├── sleep.csv
│   │   ├── steps.csv
│   │   ├── screentime.csv
│   │   ├── accuweather.csv
│   │   ├── google_calendar.csv
│   │   └── notification.json
│   ├── interim/
│   │   └── daily_records.json     # 일별 통합 레코드
│   └── processed/
│       ├── weekly_summary.json    # 주별 요약
│       ├── baseline.json          # 개인 베이스라인 (전체 기간 평균)
│       └── weekly_score.json      # 주별 건강 점수 (백엔드 전달용)
│
├── summaries/
│   ├── daily/                     # 일별 자연어 요약 텍스트
│   │   └── YYYY-MM-DD.txt
│   └── weekly/                    # 주별 자연어 요약 텍스트
│       └── YYYY-WXX.txt
│
├── weekly_reports/                # LLM 분석 결과
│   ├── weekly_YYYY-WXX.txt        # 주간 리포트 (점수 블록 포함)
│   └── weekly_YYYY-WXX.json       # 주간 리포트 JSON (백엔드 전달용)
│
└── src/
    ├── model/
    │   ├── parsers.py                  # 도메인별 Raw 데이터 파서
    │   ├── build_llm_input_summary.py  # 전처리 데이터 → 자연어 요약 변환
    │   ├── evidence.py                 # 통계 근거 블록 생성
    │   ├── llm_client.py               # Ollama LLM 호출 클라이언트
    │   └── scorer.py                   # 주간 건강 점수 계산기
    └── utils/
        ├── paths.py                    # 프로젝트 경로 중앙 관리
        ├── helpers.py                  # 공통 유틸리티 함수
        └── constants.py               # 공통 상수 및 매핑 테이블
```

---

## 실행 순서

### Step 1 — 전처리

```bash
python run_weekly_llm_report.py
```

`data/raw/` 의 원본 데이터를 파싱·통합해 JSON과 자연어 요약 파일을 생성합니다.

**출력 파일:**
- `data/interim/daily_records.json` — 일별 통합 레코드
- `data/processed/weekly_summary.json` — 주별 요약
- `data/processed/baseline.json` — 전체 기간 기준 개인 평균
- `summaries/daily/YYYY-MM-DD.txt` — 일별 자연어 요약
- `summaries/weekly/YYYY-WXX.txt` — 주별 자연어 요약

### Step 2 — LLM 분석 + 점수 계산

```bash
# 특정 주차 분석
python run_llm_analysis_with_score.py --week 2025-W47

# 점수만 계산 (LLM 호출 없음)
python run_llm_analysis_with_score.py --week 2025-W47 --score-only

# 전체 주차 분석
python run_llm_analysis_with_score.py --all-weeks
```

**출력 파일:**
- `weekly_reports/weekly_YYYY-WXX.txt` — 점수 블록 + LLM 리포트
- `weekly_reports/weekly_YYYY-WXX.json` — 리포트 JSON (백엔드 전달용)
- `data/processed/weekly_score.json` — 전체 주차 점수 누적 JSON (백엔드 전달용)

---

## 각 파일 역할

### 실행 파일

| 파일 | 역할 |
|------|------|
| `run_weekly_llm_report.py` | Raw 데이터 파싱 → JSON·요약 파일 생성 |
| `run_llm_analysis_with_score.py` | LLM 분석 + 점수 계산 + JSON 저장 |

### src/model/

| 파일 | 역할 |
|------|------|
| `parsers.py` | 수면·걸음수·스크린타임·날씨·캘린더·금융 CSV/JSON 파싱 |
| `build_llm_input_summary.py` | 파싱된 데이터 → 베이스라인 계산, 일별·주별 자연어 요약 생성 |
| `evidence.py` | 주간 데이터의 통계(상관관계, 이상치, 극값 등) 근거 블록 생성 |
| `llm_client.py` | Ollama 연결 확인, 일간·주간 분석 프롬프트 전송 및 응답 수신 |
| `scorer.py` | 수면·활동·스크린타임·소비 4개 항목 점수 계산 (총 100점) |

### src/utils/

| 파일 | 역할 |
|------|------|
| `paths.py` | 프로젝트 전체 파일 경로 중앙 관리 |
| `helpers.py` | UTC↔KST 변환, 수면 날짜 할당, 카테고리 분류 등 공통 함수 |
| `constants.py` | 앱 패키지명 매핑, 캘린더 카테고리, 거래처 카테고리, 날씨 한글 변환 |

---

## 처리된 데이터 저장 위치

| 데이터 | 경로 | 설명 |
|--------|------|------|
| 일별 통합 레코드 | `data/interim/daily_records.json` | 모든 도메인을 날짜 키로 통합 |
| 주별 요약 | `data/processed/weekly_summary.json` — | ISO 주차 기준 집계 |
| 개인 베이스라인 | `data/processed/baseline.json` | 전체 기간 평균 (수면·걸음수·스크린타임) |
| 주간 건강 점수 | `data/processed/weekly_score.json` | 백엔드 전달용, period 포함 |
| 주간 리포트 JSON | `weekly_reports/weekly_YYYY-WXX.json` | 백엔드 전달용, period + report_text 포함 |

---

## 🔧 환경 설정

### 필요 사항
- Python 3.10+
- [Ollama](https://ollama.com) 설치 및 실행
- 모델 설치: `ollama pull qwen2.5:7b`

### 패키지 설치

```bash
pip install -r requirements.txt
```

### Ollama 서버 실행 확인

```bash
ollama serve
```

---

## 건강 점수 기준

| 항목 | 배점 | 기준 |
|------|------|------|
| 수면 | 30점 | 평균 7~9시간, 불안정성 페널티 |
| 활동 | 25점 | 일평균 걸음수 10,000보 목표 |
| 스크린타임 | 25점 | 일 360분 이하, 오락 120분 이하 |
| 소비 | 20점 | 주 420,000원 이하, 집중도 페널티 |

등급: **A**(90~) **B**(75~) **C**(55~) **D**(35~) **E**(~35)
