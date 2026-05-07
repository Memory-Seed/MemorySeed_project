# MemorySeed — AI 서버 협업 스펙

> **대상**: AI 파트 담당자
> **목적**: 백엔드(Spring Boot)에서 AI 서버(FastAPI)로 보내는 요청/응답 JSON 규격 정의
> **작성일**: 2026-05-07

---

## 1. 변경의 핵심

기존 AI 서버는 로컬 JSON 파일에서 더미 데이터를 읽어 동작합니다.
**앞으로는 백엔드가 DB에서 조회한 실제 유저 데이터를 Request Body에 담아 전달**할 예정이니, 모든 엔드포인트에서 `lifelog_data` 필드를 추가로 받아 처리해주세요.

기존 로직(LLM 호출, 이상치 감지, 카테고리 매핑 등)은 그대로 두고 **데이터 입력 소스만 파일 → request body로 변경**하시면 됩니다.

---

## 2. 공통 — `lifelog_data` 구조

모든 AI 엔드포인트의 Request Body에 **공통적으로** 들어가는 필드입니다.
백엔드의 `GET /api/lifelog/raw` 응답 JSON과 **동일한 구조**입니다.

```json
{
  "lifelog_data": {
    "transactions": [
      {
        "id": 1,
        "runId": 10,
        "timestamp": "2026-05-07T14:30:00",
        "amountKrw": 15000,
        "merchant": "스타벅스"
      }
    ],
    "screenTimes": [
      {
        "id": 1,
        "runId": 10,
        "appPackage": "com.google.android.youtube",
        "startTime": "2026-05-07T20:00:00",
        "endTime": "2026-05-07T21:30:00",
        "durationSec": 5400
      }
    ],
    "sleeps": [
      {
        "id": 1,
        "runId": 10,
        "startTime": "2026-05-07T00:30:00",
        "endTime": "2026-05-07T07:00:00",
        "durationMin": 390
      }
    ],
    "steps": [
      {
        "id": 1,
        "runId": 10,
        "time": "2026-05-07T10:00:00",
        "stepCount": 1200
      }
    ],
    "weathers": [
      {
        "id": 1,
        "runId": 10,
        "time": "2026-05-07T09:00:00",
        "temperatureC": 22.5,
        "pm10": 30,
        "condition": "Sunny"
      }
    ]
  }
}
```

| 필드 | 타입 | 설명 |
|---|---|---|
| `transactions` | array | 결제/지출 이벤트 |
| `screenTimes` | array | 앱별 사용 시간 세션 |
| `sleeps` | array | 수면 세션 |
| `steps` | array | 시간대별 걸음수 |
| `weathers` | array | 시간대별 날씨/대기질 |

> 🟡 **각 배열은 빈 배열(`[]`)일 수 있습니다.** 데이터가 없으면 빈 상태로 옵니다. 안전하게 처리해주세요.

---

## 3. 엔드포인트별 스펙

### 3-1. `POST /analyze` — 일일 퀘스트 추천

#### Request Body
```json
{
  "diary_text": "오늘 너무 피곤해서 운동을 못했다. 자꾸 유튜브만 보게 된다.",
  "category": "EXERCISE",
  "target_date": "2026-05-07",
  "lifelog_data": { ... 위 공통 구조 ... }
}
```

| 필드 | 타입 | 필수 | 설명 |
|---|---|---|---|
| `diary_text` | string | 선택 | 유저 일기 (최대 2000자, null 가능) |
| `category` | string | 필수 | 퀘스트 카테고리 (아래 enum) |
| `target_date` | string (YYYY-MM-DD) | 필수 | 대상 날짜 |
| `lifelog_data` | object | 필수 | 위 공통 구조 |

**category enum**: `SLEEP, STUDY, EXERCISE, HEALTH, DIGITAL_DETOX, ETC`

#### Response Body (기존 그대로 유지)
```json
{
  "date": "2026-05-07",
  "greeting": "오늘도 화이팅!",
  "quests": [
    {
      "id": "q1",
      "text": "가벼운 스트레칭 10분",
      "description": "피로가 쌓인 날엔 무리한 운동보다 가벼운 스트레칭이 좋아요.",
      "isDone": false,
      "coinReward": 10,
      "affinityReward": 5,
      "type": "exercise",
      "difficulty": "EASY",
      "targetValue": 10,
      "period": "daily"
    }
  ],
  "hiddenQuests": []
}
```

> 백엔드는 `quests` 배열의 모든 퀘스트를 DB에 저장합니다.

---

### 3-2. `POST /report/weekly` — 주간 리포트

#### Request Body
```json
{
  "start_date": "2026-05-04",
  "end_date": "2026-05-10",
  "lifelog_data": { ... 공통 구조 (7일치 데이터) ... }
}
```

| 필드 | 타입 | 필수 | 설명 |
|---|---|---|---|
| `start_date` | string (YYYY-MM-DD) | 필수 | 주 시작일 (월요일) |
| `end_date` | string (YYYY-MM-DD) | 필수 | 주 종료일 (일요일) |
| `lifelog_data` | object | 필수 | 7일치 데이터 |

#### Response Body (기존 그대로 유지)
```json
{
  "weekly_summary": "이번 주는 평균 수면 6시간으로 다소 부족했습니다.",
  "top_emotion": "피로",
  "growth_tip": "다음 주는 매일 30분 일찍 잠들어보세요.",
  "weekly_score": 72
}
```

---

### 3-3. `POST /report/monthly` — 월간 리포트

#### Request Body
```json
{
  "year_month": "2026-05",
  "lifelog_data": { ... 공통 구조 (한 달치 데이터) ... }
}
```

| 필드 | 타입 | 필수 | 설명 |
|---|---|---|---|
| `year_month` | string (YYYY-MM) | 필수 | 대상 월 |
| `lifelog_data` | object | 필수 | 한 달치 데이터 |

#### Response Body (확정 필요)
백엔드는 일단 아래 구조로 가정하고 매핑 코드를 작성해뒀습니다. **변경하실 거면 알려주세요.**

```json
{
  "monthly_summary": "5월은 운동량이 4월 대비 20% 증가했습니다.",
  "top_emotion": "활력",
  "growth_tip": "이 페이스를 유지해보세요!",
  "monthly_score": 85
}
```

---

## 4. 처리 시간 / 비동기 관련

- **`/report/weekly`, `/report/monthly`** 는 백엔드에서 **비동기**로 호출합니다.
  - 백엔드는 요청을 받자마자 DB에 PENDING 상태로 저장 후 클라이언트에 즉시 응답
  - 그 다음 백그라운드로 AI 서버 호출 → 결과를 DB 업데이트
  - 따라서 AI 서버 응답이 좀 느려도 (~30초 이상) 괜찮습니다.

- **`/analyze`** 는 **동기 호출**입니다. 가능하면 **10초 이내** 응답 부탁드려요.

---

## 5. 에러 응답 권장 포맷

```json
{
  "detail": "에러 사유"
}
```

- HTTP 상태코드: 4xx (잘못된 요청) / 5xx (서버 내부 에러)
- 백엔드는 AI 서버가 응답하지 않거나 5xx가 와도 자체 fallback 처리하므로 전체가 죽지는 않지만, 가능하면 명확한 에러 메시지 부탁드립니다.

---

## 6. 배포 환경

| 항목 | 값 |
|---|---|
| 호스트 | EC2 내부, `localhost:8000` |
| 통신 | HTTP (HTTPS 아님, 같은 EC2 컨테이너 간 통신) |
| 포트 | **8000 고정** |
| 컨테이너 이름 권장 | `ai-server` 또는 비슷하게 |

---

## 7. 헬스체크

`GET /health` 엔드포인트는 그대로 유지해주세요. 백엔드에서 향후 헬스체크 용도로 사용할 수 있습니다.

---

## 8. 체크리스트 (AI 파트)

- [ ] `/analyze`, `/report/weekly`, `/report/monthly` Request Body에 `lifelog_data` 필드 받기
- [ ] `lifelog_data` 안의 5개 배열(`transactions`, `screenTimes`, `sleeps`, `steps`, `weathers`)을 각각 빈 배열에도 안전하게 처리
- [ ] 기존 파일 기반 데이터 로드 로직을 `lifelog_data` 입력으로 교체
- [ ] Response 구조 유지 (혹시 변경하면 백엔드 담당자에게 알리기)
- [ ] Docker 이미지 빌드 후 이미지명 공유 (또는 `.tar`)

---

## 부록 A. 백엔드에서 사용하는 정확한 Request 코드 (참고)

```java
// AiApiClient.java
public record AnalyzeRequest(
    @JsonProperty("diary_text")    String diaryText,
                                    String category,
    @JsonProperty("target_date")   LocalDate targetDate,
    @JsonProperty("lifelog_data")  LifelogRawResponse lifelogData
) {}

public record WeeklyReportRequest(
    @JsonProperty("start_date")    LocalDate startDate,
    @JsonProperty("end_date")      LocalDate endDate,
    @JsonProperty("lifelog_data")  LifelogRawResponse lifelogData
) {}

public record MonthlyReportRequest(
    @JsonProperty("year_month")    String yearMonth,
    @JsonProperty("lifelog_data")  LifelogRawResponse lifelogData
) {}
```

위 코드의 JSON 직렬화 결과가 **그대로** AI 서버에 도달합니다.
