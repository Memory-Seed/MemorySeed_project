package com.memoryseed.backend.domain.report.dto;

import com.memoryseed.backend.domain.report.entity.MonthlyReport;
import com.memoryseed.backend.domain.report.entity.ReportStatus;

public record MonthlyReportResponse(
        Long id,
        String yearMonth,
        ReportStatus status,
        String monthlySummary,
        String topEmotion,
        String growthTip,
        Integer monthlyScore,
        String errorMessage
) {
    public static MonthlyReportResponse from(MonthlyReport r) {
        return new MonthlyReportResponse(
                r.getId(),
                r.getYearMonth(),
                r.getStatus(),
                r.getMonthlySummary(),
                r.getTopEmotion(),
                r.getGrowthTip(),
                r.getMonthlyScore(),
                r.getErrorMessage()
        );
    }
}
