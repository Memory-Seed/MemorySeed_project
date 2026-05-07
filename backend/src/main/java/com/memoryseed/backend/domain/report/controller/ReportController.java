package com.memoryseed.backend.domain.report.controller;

import com.memoryseed.backend.domain.report.dto.MonthlyReportResponse;
import com.memoryseed.backend.domain.report.dto.WeeklyReportResponse;
import com.memoryseed.backend.domain.report.service.ReportService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/report")
@RequiredArgsConstructor
public class ReportController {

    private final ReportService reportService;

    // ── 주간 리포트 ─────────────────────────────────────────────

    /**
     * 주간 리포트 생성 요청 (비동기).
     * 이미 PENDING 또는 DONE 레코드가 있으면 그것을 반환 (중복 요청 방지).
     */
    @PostMapping("/weekly")
    public ResponseEntity<WeeklyReportResponse> createWeeklyReport(Authentication authentication) {
        String providerId = authentication.getName();
        WeeklyReportResponse response = reportService.requestWeeklyReport(providerId);
        // 새로 시작된 경우 202, 이미 존재하는 경우 200
        HttpStatus status = (response.status().name().equals("PENDING") && response.weeklySummary() == null)
                ? HttpStatus.ACCEPTED : HttpStatus.OK;
        return ResponseEntity.status(status).body(response);
    }

    /**
     * 가장 최근 주간 리포트 조회 (폴링용).
     */
    @GetMapping("/weekly/latest")
    public ResponseEntity<WeeklyReportResponse> getLatestWeeklyReport(Authentication authentication) {
        String providerId = authentication.getName();
        return ResponseEntity.ok(reportService.getLatestWeeklyReport(providerId));
    }

    @GetMapping("/weekly")
    public ResponseEntity<List<WeeklyReportResponse>> listWeeklyReports(Authentication authentication) {
        String providerId = authentication.getName();
        return ResponseEntity.ok(reportService.listWeeklyReports(providerId));
    }

    // ── 월간 리포트 ─────────────────────────────────────────────

    @PostMapping("/monthly")
    public ResponseEntity<MonthlyReportResponse> createMonthlyReport(Authentication authentication) {
        String providerId = authentication.getName();
        MonthlyReportResponse response = reportService.requestMonthlyReport(providerId);
        HttpStatus status = (response.status().name().equals("PENDING") && response.monthlySummary() == null)
                ? HttpStatus.ACCEPTED : HttpStatus.OK;
        return ResponseEntity.status(status).body(response);
    }

    @GetMapping("/monthly/latest")
    public ResponseEntity<MonthlyReportResponse> getLatestMonthlyReport(Authentication authentication) {
        String providerId = authentication.getName();
        return ResponseEntity.ok(reportService.getLatestMonthlyReport(providerId));
    }

    @GetMapping("/monthly")
    public ResponseEntity<List<MonthlyReportResponse>> listMonthlyReports(Authentication authentication) {
        String providerId = authentication.getName();
        return ResponseEntity.ok(reportService.listMonthlyReports(providerId));
    }
}
