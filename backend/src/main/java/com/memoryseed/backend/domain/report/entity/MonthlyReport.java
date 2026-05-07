package com.memoryseed.backend.domain.report.entity;

import com.memoryseed.backend.domain.user.entity.User;
import com.memoryseed.backend.global.entity.BaseTimeEntity;
import jakarta.persistence.*;
import lombok.AccessLevel;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Entity
@Table(
        name = "monthly_reports",
        uniqueConstraints = @UniqueConstraint(
                name = "uk_monthly_report_user_month",
                columnNames = {"user_id", "year_month"}
        ),
        indexes = @Index(name = "idx_monthly_report_user", columnList = "user_id")
)
@Getter
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class MonthlyReport extends BaseTimeEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "user_id", nullable = false)
    private User user;

    // YYYY-MM 형식 (예: "2025-05")
    @Column(name = "year_month", length = 7, nullable = false)
    private String yearMonth;

    @Enumerated(EnumType.STRING)
    @Column(length = 20, nullable = false)
    private ReportStatus status;

    @Column(columnDefinition = "TEXT")
    private String monthlySummary;

    @Column(length = 50)
    private String topEmotion;

    @Column(columnDefinition = "TEXT")
    private String growthTip;

    private Integer monthlyScore;

    @Column(columnDefinition = "TEXT")
    private String errorMessage;

    public MonthlyReport(User user, String yearMonth) {
        this.user = user;
        this.yearMonth = yearMonth;
        this.status = ReportStatus.PENDING;
    }

    public void markDone(String summary, String emotion, String tip, Integer score) {
        this.status = ReportStatus.DONE;
        this.monthlySummary = summary;
        this.topEmotion = emotion;
        this.growthTip = tip;
        this.monthlyScore = score;
        this.errorMessage = null;
    }

    public void markFailed(String reason) {
        this.status = ReportStatus.FAILED;
        this.errorMessage = reason;
    }
}
