"""
main.py
LifeQuest AI FastAPI 서버

엔드포인트:
  POST /analyze         → 일일 퀘스트 생성
  POST /report/weekly   → 주간 리포트 생성
  POST /report/monthly  → 월간 리포트 생성
"""

from datetime import date, datetime, timedelta, timezone
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from models import AnalyzeRequest, WeeklyReportRequest, MonthlyReportRequest, LifelogData
from daily_quest import DailyQuestGenerator
from weekly_report import WeeklyReportGenerator
from monthly_report import MonthlyReportGenerator
from src.preprocessor import LifeDataPreprocessor
from src.llm_caller import LLMCaller

KST = timezone(timedelta(hours=9))


# ── lifelog_data → LifeDataPreprocessor 변환 ──

def _kst_str(dt: datetime) -> str:
    """naive datetime을 KST로 간주해 ISO 문자열로 변환"""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=KST)
    return dt.isoformat()


def build_preprocessor_from_lifelog(lifelog: LifelogData) -> LifeDataPreprocessor:
    sleep_list = [
        {"startTime": _kst_str(s.startTime), "endTime": _kst_str(s.endTime)}
        for s in lifelog.sleeps
    ]

    steps_list = [
        {"startTime": _kst_str(s.time), "count": s.stepCount}
        for s in lifelog.steps
    ]

    screentime_list = [
        {
            "firstTimeStamp":       int((s.startTime.replace(tzinfo=KST) if s.startTime.tzinfo is None else s.startTime).timestamp() * 1000),
            "packageName":          s.appPackage,
            "totalTimeInForeground": s.durationSec * 1000,
        }
        for s in lifelog.screenTimes
    ]

    weather_list = [
        {
            "LocalObservationDateTime": _kst_str(w.time),
            "Temperature":              {"Metric": {"Value": w.temperatureC}},
            "RealFeelTemperature":      {"Metric": {"Value": w.temperatureC}},
            "RelativeHumidity":         None,
            "PrecipitationProbability": 0,
            "WeatherText":              w.condition,
        }
        for w in lifelog.weathers
    ]

    transactions_list = [
        {"timestamp": _kst_str(t.timestamp), "amountKrw": t.amountKrw, "merchant": t.merchant}
        for t in lifelog.transactions
    ]

    return LifeDataPreprocessor(
        sleep=sleep_list,
        steps=steps_list,
        screentime=screentime_list,
        calendar={"items": []},
        notification=[],
        weather=weather_list,
        transactions=transactions_list,
    )


# ── 앱 초기화 ────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.llm_caller = LLMCaller()
    print("✅ LifeQuest AI 서버 준비 완료")
    yield

app = FastAPI(
    title="LifeQuest AI API",
    description="일일 퀘스트 / 주간 리포트 / 월간 리포트 생성 API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── 헬스체크 ─────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "service": "LifeQuest AI"}


# ── 카테고리 → 내부 카테고리 매핑 ─────────────

CATEGORY_TO_INTERNAL = {
    "SLEEP":         "수면",
    "EXERCISE":      "운동",
    "DIGITAL_DETOX": "스크린타임",
    "STUDY":         "생산성",
    "HEALTH":        "건강",
    "ETC":           "지출",
}


# ── 1. 일일 퀘스트 (POST /analyze) ───────────

@app.post("/analyze")
async def analyze(req: AnalyzeRequest):
    """
    일일 퀘스트 생성
    - category 필수, diary_text 선택
    - category 기반으로 퀘스트 1개 반환
    - due_days < 7 → 백엔드에서 daily 처리
    """
    try:
        pp     = build_preprocessor_from_lifelog(req.lifelog_data)
        caller = app.state.llm_caller
        target = req.target_date or date.today()

        result = DailyQuestGenerator(pp, caller).generate(
            target,
            diary_text=req.diary_text,
            category=req.category,
        )
        raw = result.to_api_format()

        # category에 해당하는 퀘스트 1개 추출
        internal_category = CATEGORY_TO_INTERNAL.get(req.category, "")
        all_quests = raw.get("quests", [])

        # 1순위: category 매칭 퀘스트
        matched = next(
            (q for q in all_quests if q.get("type", "").upper() == req.category.lower()
             or CATEGORY_TO_INTERNAL.get(req.category, "") in q.get("type", "")),
            None,
        )
        # 2순위: 그냥 첫 번째
        quest = matched or (all_quests[0] if all_quests else None)

        if not quest:
            raise HTTPException(status_code=500, detail="퀘스트 생성 실패")

        due_days = 7 if quest.get("period") == "weekly" else 1

        return {
            "title":        quest.get("text", ""),
            "description":  quest.get("description", ""),
            "target_value": int(quest["targetValue"]) if quest.get("targetValue") else None,
            "due_days":     due_days,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── 2. 주간 리포트 (POST /report/weekly) ─────

@app.post("/report/weekly")
async def weekly_report(req: WeeklyReportRequest):
    """
    주간 리포트 생성
    - start_date / end_date 미입력 시 지난 주 (월~일) 자동 계산
    - Response: weekly_summary, top_emotion, growth_tip, weekly_score
    """
    try:
        pp     = build_preprocessor_from_lifelog(req.lifelog_data)
        caller = app.state.llm_caller

        if req.start_date and req.end_date:
            start = req.start_date
            end   = req.end_date
        else:
            today = date.today()
            start = today - timedelta(days=today.weekday() + 7)
            end   = start + timedelta(days=6)

        result = WeeklyReportGenerator(pp, caller).generate(start, end)
        return result.to_api_format()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── 3. 월간 리포트 (POST /report/monthly) ────

@app.post("/report/monthly")
async def monthly_report(req: MonthlyReportRequest):
    """
    월간 리포트 생성
    - year_month 미입력 시 이번 달 기준
    - Response: monthly_insight, main_keyword, monthly_score, cheering_message
    """
    try:
        pp     = build_preprocessor_from_lifelog(req.lifelog_data)
        caller = app.state.llm_caller

        if req.year_month:
            year, month = map(int, req.year_month.split("-"))
        else:
            today = date.today()
            year, month = today.year, today.month

        result = MonthlyReportGenerator(pp, caller).generate(year, month)
        return result.to_api_format()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))