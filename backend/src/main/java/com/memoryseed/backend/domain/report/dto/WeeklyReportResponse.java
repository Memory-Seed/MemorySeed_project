package com.memoryseed.backend.domain.report.dto;

import com.memoryseed.backend.domain.report.entity.ReportStatus;
import com.memoryseed.backend.domain.report.entity.WeeklyReport;

import java.time.LocalDate;

public record WeeklyReportResponse(
        Long id,
        LocalDate weekStartDate,
        LocalDate weekEndDate,
        ReportStatus status,
        String weeklySummary,
        String topEmotion,
        String growthTip,
        Integer weeklyScore,
        String errorMessage
) {
    public static WeeklyReportResponse from(WeeklyReport r) {
        return new WeeklyReportResponse(
                r.getId(),
                r.getWeekStartDate(),
                r.getWeekEndDate(),
                r.getStatus(),
                r.getWeeklySummary(),
                r.getTopEmotion(),
                r.getGrowthTip(),
                r.getWeeklyScore(),
                r.getErrorMessage()
        );
    }
}
