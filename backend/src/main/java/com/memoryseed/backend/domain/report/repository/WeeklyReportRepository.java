package com.memoryseed.backend.domain.report.repository;

import com.memoryseed.backend.domain.report.entity.ReportStatus;
import com.memoryseed.backend.domain.report.entity.WeeklyReport;
import com.memoryseed.backend.domain.user.entity.User;
import org.springframework.data.jpa.repository.JpaRepository;

import java.time.LocalDate;
import java.util.List;
import java.util.Optional;

public interface WeeklyReportRepository extends JpaRepository<WeeklyReport, Long> {
    Optional<WeeklyReport> findByUserAndWeekStartDate(User user, LocalDate weekStartDate);
    boolean existsByUserAndStatus(User user, ReportStatus status);
    List<WeeklyReport> findByUserOrderByWeekStartDateDesc(User user);
}
