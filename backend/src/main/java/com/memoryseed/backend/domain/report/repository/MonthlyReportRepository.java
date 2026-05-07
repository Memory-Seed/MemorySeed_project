package com.memoryseed.backend.domain.report.repository;

import com.memoryseed.backend.domain.report.entity.MonthlyReport;
import com.memoryseed.backend.domain.report.entity.ReportStatus;
import com.memoryseed.backend.domain.user.entity.User;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;

public interface MonthlyReportRepository extends JpaRepository<MonthlyReport, Long> {
    Optional<MonthlyReport> findByUserAndYearMonth(User user, String yearMonth);
    boolean existsByUserAndStatus(User user, ReportStatus status);
    List<MonthlyReport> findByUserOrderByYearMonthDesc(User user);
}
