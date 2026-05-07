package com.memoryseed.backend.domain.ai.client;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.memoryseed.backend.domain.lifelog.dto.LifelogRawResponse;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestTemplate;

import java.time.LocalDate;
import java.util.Collections;
import java.util.List;

/**
 * AI 분석 서버(Python FastAPI, localhost:8000)와 통신하는 클라이언트.
 *
 * 모든 요청에는 백엔드 DB에서 조회한 lifelog 데이터를 포함하여 전송합니다.
 * AI 서버는 LifelogRawResponse 형식 그대로 사용합니다 (AI팀과 협의 완료).
 *
 * 엔드포인트:
 *  - POST /analyze         : 일일 퀘스트 추천 (quests 배열 반환)
 *  - POST /report/weekly   : 주간 리포트 생성
 *  - POST /report/monthly  : 월간 리포트 생성
 */
@Slf4j
@Component
public class AiApiClient {

    private final RestTemplate restTemplate;
    private final String aiApiUrl;

    public AiApiClient(RestTemplate restTemplate,
                       @Value("${ai.api-url}") String aiApiUrl) {
        this.restTemplate = restTemplate;
        this.aiApiUrl = aiApiUrl;
    }

    /**
     * 일일 퀘스트 추천. AI 서버 미연결 시 빈 리스트 반환.
     */
    public List<AiQuest> recommendDaily(String category, String diaryText, LocalDate targetDate, LifelogRawResponse lifelog) {
        try {
            AnalyzeRequest req = new AnalyzeRequest(diaryText, category, targetDate, lifelog);
            AnalyzeResponse res = restTemplate.postForObject(
                    aiApiUrl + "/analyze",
                    req,
                    AnalyzeResponse.class
            );
            if (res == null || res.quests() == null) {
                log.warn("AI /analyze 빈 응답.");
                return Collections.emptyList();
            }
            return res.quests();
        } catch (RestClientException e) {
            log.warn("AI /analyze 호출 실패: {}", e.getMessage());
            return Collections.emptyList();
        }
    }

    /**
     * 주간 리포트 생성. AI 서버 미연결 시 null 반환.
     */
    public WeeklyReportResult requestWeeklyReport(LocalDate startDate, LocalDate endDate, LifelogRawResponse lifelog) {
        try {
            WeeklyReportRequest req = new WeeklyReportRequest(startDate, endDate, lifelog);
            return restTemplate.postForObject(
                    aiApiUrl + "/report/weekly",
                    req,
                    WeeklyReportResult.class
            );
        } catch (RestClientException e) {
            log.warn("AI /report/weekly 호출 실패: {}", e.getMessage());
            return null;
        }
    }

    /**
     * 월간 리포트 생성. AI 서버 미연결 시 null 반환.
     */
    public MonthlyReportResult requestMonthlyReport(String yearMonth, LifelogRawResponse lifelog) {
        try {
            MonthlyReportRequest req = new MonthlyReportRequest(yearMonth, lifelog);
            return restTemplate.postForObject(
                    aiApiUrl + "/report/monthly",
                    req,
                    MonthlyReportResult.class
            );
        } catch (RestClientException e) {
            log.warn("AI /report/monthly 호출 실패: {}", e.getMessage());
            return null;
        }
    }

    // ── /analyze Request ─────────────────────────────────────────────
    public record AnalyzeRequest(
            @JsonProperty("diary_text") String diaryText,
            String category,
            @JsonProperty("target_date") LocalDate targetDate,
            @JsonProperty("lifelog_data") LifelogRawResponse lifelogData
    ) {}

    // ── /analyze Response ────────────────────────────────────────────
    public record AnalyzeResponse(
            String date,
            String greeting,
            List<AiQuest> quests,
            @JsonProperty("hiddenQuests") List<AiQuest> hiddenQuests
    ) {}

    public record AiQuest(
            String id,
            String text,           // 퀘스트 제목
            String description,
            @JsonProperty("isDone") Boolean isDone,
            @JsonProperty("coinReward") Integer coinReward,
            @JsonProperty("affinityReward") Integer affinityReward,
            String type,           // 카테고리 (소문자)
            String difficulty,     // EASY / NORMAL / HARD / HIDDEN
            @JsonProperty("targetValue") Integer targetValue,
            String period          // "daily"
    ) {}

    // ── /report/weekly Request ───────────────────────────────────────
    public record WeeklyReportRequest(
            @JsonProperty("start_date") LocalDate startDate,
            @JsonProperty("end_date") LocalDate endDate,
            @JsonProperty("lifelog_data") LifelogRawResponse lifelogData
    ) {}

    // ── /report/weekly Response ──────────────────────────────────────
    public record WeeklyReportResult(
            @JsonProperty("weekly_summary") String weeklySummary,
            @JsonProperty("top_emotion") String topEmotion,
            @JsonProperty("growth_tip") String growthTip,
            @JsonProperty("weekly_score") Integer weeklyScore
    ) {}

    // ── /report/monthly Request ──────────────────────────────────────
    public record MonthlyReportRequest(
            @JsonProperty("year_month") String yearMonth,
            @JsonProperty("lifelog_data") LifelogRawResponse lifelogData
    ) {}

    // ── /report/monthly Response ─────────────────────────────────────
    // (AI팀과 최종 필드 협의 후 조정 가능. 일단 weekly와 동일 구조로 가정)
    public record MonthlyReportResult(
            @JsonProperty("monthly_summary") String monthlySummary,
            @JsonProperty("top_emotion") String topEmotion,
            @JsonProperty("growth_tip") String growthTip,
            @JsonProperty("monthly_score") Integer monthlyScore
    ) {}
}
