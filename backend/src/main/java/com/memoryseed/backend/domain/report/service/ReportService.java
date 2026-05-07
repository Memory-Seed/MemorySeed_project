package com.memoryseed.backend.domain.report.service;

import com.memoryseed.backend.domain.ai.client.AiApiClient;
import com.memoryseed.backend.domain.lifelog.dto.LifelogRawResponse;
import com.memoryseed.backend.domain.lifelog.service.LifelogQueryService;
import com.memoryseed.backend.domain.report.dto.MonthlyReportResponse;
import com.memoryseed.backend.domain.report.dto.WeeklyReportResponse;
import com.memoryseed.backend.domain.report.entity.MonthlyReport;
import com.memoryseed.backend.domain.report.entity.ReportStatus;
import com.memoryseed.backend.domain.report.entity.WeeklyReport;
import com.memoryseed.backend.domain.report.repository.MonthlyReportRepository;
import com.memoryseed.backend.domain.report.repository.WeeklyReportRepository;
import com.memoryseed.backend.domain.user.entity.User;
import com.memoryseed.backend.domain.user.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.DayOfWeek;
import java.time.LocalDate;
import java.time.YearMonth;
import java.time.format.DateTimeFormatter;
import java.util.List;
import java.util.NoSuchElementException;

/**
 * 주간/월간 리포트 생성 서비스.
 *
 * 흐름:
 *  1) POST 요청 시 PENDING 상태로 즉시 DB 저장 (중복 방지)
 *  2) @Async 메서드로 AI 서버 호출
 *  3) 완료 시 DONE / 실패 시 FAILED로 상태 업데이트
 *
 * 클라이언트는 GET으로 폴링하여 완료 여부 확인.
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class ReportService {

    private final UserRepository userRepository;
    private final WeeklyReportRepository weeklyReportRepository;
    private final MonthlyReportRepository monthlyReportRepository;
    private final LifelogQueryService lifelogQueryService;
    private final AiApiClient aiApiClient;

    private static final DateTimeFormatter YEAR_MONTH_FMT = DateTimeFormatter.ofPattern("yyyy-MM");

    // ── 주간 리포트 ─────────────────────────────────────────────

    /**
     * 주간 리포트 생성 요청. 이미 PENDING 또는 DONE이면 기존 레코드 반환.
     */
    @Transactional
    public WeeklyReportResponse requestWeeklyReport(String providerId) {
        User user = getUser(providerId);

        // 이번 주 월요일 계산
        LocalDate today = LocalDate.now();
        LocalDate weekStart = today.with(DayOfWeek.MONDAY);
        LocalDate weekEnd = weekStart.plusDays(6);

        // 이미 존재하면 그것을 반환 (중복 방지)
        var existing = weeklyReportRepository.findByUserAndWeekStartDate(user, weekStart);
        if (existing.isPresent()) {
            return WeeklyReportResponse.from(existing.get());
        }

        // PENDING 상태로 즉시 저장
        WeeklyReport report = weeklyReportRepository.save(
                new WeeklyReport(user, weekStart, weekEnd)
        );

        // 비동기로 AI 서버 호출
        generateWeeklyReportAsync(report.getId(), providerId, weekStart, weekEnd);

        return WeeklyReportResponse.from(report);
    }

    @Async
    @Transactional
    public void generateWeeklyReportAsync(Long reportId, String providerId, LocalDate weekStart, LocalDate weekEnd) {
        try {
            LifelogRawResponse lifelog = lifelogQueryService.getRawLifelogs(providerId, weekStart, weekEnd);
            AiApiClient.WeeklyReportResult result = aiApiClient.requestWeeklyReport(weekStart, weekEnd, lifelog);

            WeeklyReport report = weeklyReportRepository.findById(reportId)
                    .orElseThrow(() -> new NoSuchElementException("WeeklyReport not found: " + reportId));

            if (result == null) {
                report.markFailed("AI 서버 응답 없음");
                return;
            }
            report.markDone(result.weeklySummary(), result.topEmotion(), result.growthTip(), result.weeklyScore());
        } catch (Exception e) {
            log.error("주간 리포트 생성 실패. reportId={}", reportId, e);
            weeklyReportRepository.findById(reportId).ifPresent(r -> r.markFailed(e.getMessage()));
        }
    }

    @Transactional(readOnly = true)
    public WeeklyReportResponse getLatestWeeklyReport(String providerId) {
        User user = getUser(providerId);
        return weeklyReportRepository.findByUserOrderByWeekStartDateDesc(user).stream()
                .findFirst()
                .map(WeeklyReportResponse::from)
                .orElseThrow(() -> new NoSuchElementException("주간 리포트가 없습니다."));
    }

    @Transactional(readOnly = true)
    public List<WeeklyReportResponse> listWeeklyReports(String providerId) {
        User user = getUser(providerId);
        return weeklyReportRepository.findByUserOrderByWeekStartDateDesc(user).stream()
                .map(WeeklyReportResponse::from)
                .toList();
    }

    // ── 월간 리포트 ─────────────────────────────────────────────

    @Transactional
    public MonthlyReportResponse requestMonthlyReport(String providerId) {
        User user = getUser(providerId);

        YearMonth currentMonth = YearMonth.now();
        String yearMonth = currentMonth.format(YEAR_MONTH_FMT);

        var existing = monthlyReportRepository.findByUserAndYearMonth(user, yearMonth);
        if (existing.isPresent()) {
            return MonthlyReportResponse.from(existing.get());
        }

        MonthlyReport report = monthlyReportRepository.save(new MonthlyReport(user, yearMonth));

        generateMonthlyReportAsync(report.getId(), providerId, currentMonth);

        return MonthlyReportResponse.from(report);
    }

    @Async
    @Transactional
    public void generateMonthlyReportAsync(Long reportId, String providerId, YearMonth yearMonth) {
        try {
            LocalDate start = yearMonth.atDay(1);
            LocalDate end = yearMonth.atEndOfMonth();
            LifelogRawResponse lifelog = lifelogQueryService.getRawLifelogs(providerId, start, end);
            AiApiClient.MonthlyReportResult result = aiApiClient.requestMonthlyReport(yearMonth.format(YEAR_MONTH_FMT), lifelog);

            MonthlyReport report = monthlyReportRepository.findById(reportId)
                    .orElseThrow(() -> new NoSuchElementException("MonthlyReport not found: " + reportId));

            if (result == null) {
                report.markFailed("AI 서버 응답 없음");
                return;
            }
            report.markDone(result.monthlySummary(), result.topEmotion(), result.growthTip(), result.monthlyScore());
        } catch (Exception e) {
            log.error("월간 리포트 생성 실패. reportId={}", reportId, e);
            monthlyReportRepository.findById(reportId).ifPresent(r -> r.markFailed(e.getMessage()));
        }
    }

    @Transactional(readOnly = true)
    public MonthlyReportResponse getLatestMonthlyReport(String providerId) {
        User user = getUser(providerId);
        return monthlyReportRepository.findByUserOrderByYearMonthDesc(user).stream()
                .findFirst()
                .map(MonthlyReportResponse::from)
                .orElseThrow(() -> new NoSuchElementException("월간 리포트가 없습니다."));
    }

    @Transactional(readOnly = true)
    public List<MonthlyReportResponse> listMonthlyReports(String providerId) {
        User user = getUser(providerId);
        return monthlyReportRepository.findByUserOrderByYearMonthDesc(user).stream()
                .map(MonthlyReportResponse::from)
                .toList();
    }

    private User getUser(String providerId) {
        return userRepository.findByProviderId(providerId)
                .orElseThrow(() -> new IllegalArgumentException("User not found: " + providerId));
    }
}
