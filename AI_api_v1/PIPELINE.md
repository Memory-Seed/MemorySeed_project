# LifeQuest — AI 분석 파이프라인

## 디렉토리 구조

```
files/
├── daily_quest.py         # 일일 퀘스트 생성 실행 파일
├── weekly_quest.py        # 주간 퀘스트 생성 실행 파일
├── daily_report.py        # 일일 리포트 생성 실행 파일
├── weekly_report.py       # 주간 리포트 생성 실행 파일
├── llm_caller.py          # Ollama LLM 호출 클라이언트
│
├── data/                  # 원본 데이터 (JSON)
│   ├── sleep.json
│   ├── steps.json
│   ├── screentime.json
│   ├── google_calendar.json
│   ├── notification.json
│   └── accuweather.json
│
├── output/                # 실행 결과 JSON (백엔드 전달용)
│   ├── daily_quest_YYYY-MM-DD.json
│   ├── weekly_quest_YYYY-MM-DD_YYYY-MM-DD.json
│   ├── daily_report_YYYY-MM-DD.json
│   └── weekly_report_YYYY-MM-DD_YYYY-MM-DD.json
│
└── src/
    ├── preprocessor.py        # 원본 JSON → 일별/주별 요약 dict 변환
    ├── anomaly_detector.py    # 이상치 탐지 (IQR + 규칙 기반)
    ├── prompt_builder.py      # LLM 프롬프트 조립 (멍코치 말투)
    └── constants.py           # 기준값, 코인 정책 상수
```

---

## 실행 방법

```bash
# 일일 퀘스트 생성
python daily_quest.py

# 주간 퀘스트 생성
python weekly_quest.py

# 일일 리포트 생성
python daily_report.py

# 주간 리포트 생성
python weekly_report.py
```

실행 시 터미널 출력과 함께 `output/` 폴더에 JSON 파일이 자동 저장됩니다.

---

## 데이터 흐름

```
data/ 원본 JSON 6종
    ↓ src/preprocessor.py
일별/주별 요약 dict
    ↓ src/anomaly_detector.py
이상치 탐지 결과
    ↓ src/prompt_builder.py
LLM 프롬프트 텍스트
    ↓ llm_caller.py (Ollama qwen2.5:7b)
퀘스트 / 리포트 JSON
    ↓
output/ 저장 + 터미널 출력
```

---

## 각 파일 역할

### 실행 파일

| 파일 | 역할 |
|------|------|
| `daily_quest.py` | 전날 데이터 기준 오늘 퀘스트 생성 + JSON 저장 |
| `weekly_quest.py` | 전 주 데이터 기준 이번 주 퀘스트 3개 생성 + JSON 저장 |
| `daily_report.py` | 오늘 데이터 기준 일일 리포트 생성 + JSON 저장 |
| `weekly_report.py` | 주간 데이터 기준 주간 리포트 생성 + JSON 저장 |

### src/

| 파일 | 역할 |
|------|------|
| `preprocessor.py` | 수면·걸음수·스크린타임·지출·일정·날씨 JSON 파싱 및 일별/주별 요약 생성 |
| `anomaly_detector.py` | 14일 히스토리 기반 IQR + 규칙 기반 이상치 탐지 |
| `prompt_builder.py` | 데이터 텍스트 변환 + 멍코치 말투 LLM 프롬프트 조립 |
| `constants.py` | 이상치 기준값, 코인 정책, 기온별 날씨 설명 상수 |

---

## 사용 데이터

| 데이터 | 파일 | 활용 |
|--------|------|------|
| 수면 | `sleep.json` | 취침/기상 시각, 수면시간 계산 |
| 걸음수 | `steps.json` | 날짜별 총 걸음수 합산 |
| 스크린타임 | `screentime.json` | 앱별 사용시간, 상위 3개 앱, 오락성 앱 탐지 |
| 캘린더 | `google_calendar.json` | 일정 목록, 공부/운동 키워드 감지 |
| 지출 | `notification.json` | KB국민은행 출금 알림 파싱 → 일별 지출/상호명 |
| 날씨 | `accuweather.json` | 기온/체감온도/습도/강수확률 → 우산·옷차림 팁 |

---

## 이상치 탐지 기준

| 항목 | 기준 | 심각도 |
|------|------|--------|
| 수면 부족 | 7h 미만 | warning / critical (4h 미만) |
| 과수면 | 9h 초과 | mild |
| 늦은 취침 | 새벽 2시 이후 | warning |
| 걸음수 부족 | 1,000보 미만 | warning |
| 스크린타임 과다 | 6시간 초과 | warning |
| 오락성 앱 과다 | 2시간 초과 | mild |
| 지출 과다 | 6만원 초과 | warning |

이상치 감지 시 퀘스트 난이도 자동 조정 (critical → easy, warning → normal)

---

## 출력 JSON 형식

### 퀘스트
```json
{
  "date": "2025-12-10",
  "greeting": "어제는 참 열심히 했구나멍!",
  "quests": [
    {
      "id": 1,
      "text": "오늘은 지갑 닫아봐요",
      "description": "어제 500,800원 썼으니 오늘은 꼭 필요한 것만 사자멍!",
      "isDone": false,
      "coinReward": 25,
      "affinityReward": 5,
      "type": "etc",
      "period": "daily",
      "targetValue": 60000,
      "difficulty": "NORMAL"
    }
  ],
  "hiddenQuests": [
    {
      "id": 1,
      "text": "우산 챙기기",
      "description": "오늘 비 예보 있으니 우산 꼭 챙겨봐멍!",
      "isDone": false,
      "coinReward": 5,
      "affinityReward": 5,
      "type": "weather",
      "period": "daily",
      "targetValue": 1,
      "difficulty": "HIDDEN"
    }
  ]
}
```

### 리포트
```json
{
  "date": "2025-12-10",
  "overallScore": 75,
  "dogComment": "오늘 일과는 잘 했지만 수면이 조금 부족했네멍!",
  "items": {
    "sleep":      { "score": 60, "data": "취침 23:52 / 기상 06:31 (6.7시간)", "feedback": "조금 더 일찍 자면 좋겠어멍!" },
    "steps":      { "score": 85, "data": "9,963보", "feedback": "만보 거의 달성했어멍!" },
    "screentime": { "score": 70, "data": "총 276분", "feedback": "오락성 앱 좀 줄여보자멍!" },
    "spending":   { "score": 40, "data": "총 234,400원 (CGV, 11번가)", "feedback": "지출이 좀 많아멍!" },
    "schedule":   { "score": 95, "data": "실습/랩, 여자친구 약속", "feedback": "일정 잘 소화했어멍!" }
  },
  "anomalyAlert": "수면 시간이 부족하고 지출이 많아 걱정돼멍.",
  "tomorrowWeather": "1.3~10.8°C, 강수확률 10%, 쌀쌀해요",
  "tomorrowComment": "내일 날씨가 추워져서 따뜻한 옷을 준비해봐요멍!"
}
```

---

## 코인 정책

| 난이도 | 코인 | 조건 |
|--------|------|------|
| Easy | 10코인 | 가볍게 달성 가능, 컨디션 저조한 날 배정 |
| Normal | 25코인 | 적당한 노력 필요 |
| Hard | 50코인 | 도전적 목표, 컨디션 좋은 날 배정 |
| Hidden | 5코인 | 날씨 조건 충족 시 자동 발동 |

---

## 환경 설정

### 필요 사항
- Python 3.10+
- [Ollama](https://ollama.com) 설치 및 실행
- 모델 설치: `ollama pull qwen2.5:7b`

### 패키지 설치
```bash
pip install openai
```

### Ollama 서버 실행 확인
```bash
ollama serve
```
