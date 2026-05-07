package com.memoryseed.backend.domain.report.entity;

import com.memoryseed.backend.domain.user.entity.User;
import com.memoryseed.backend.global.entity.BaseTimeEntity;
import jakarta.persistence.*;
import lombok.AccessLevel;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.time.LocalDate;

@Entity
@Table(
        name = "weekly_reports",
        uniqueConstraints = @UniqueConstraint(
                name = "uk_weekly_report_user_week",
                columnNames = {"user_id", "week_start_date"}
        ),
        indexes = @Index(name = "idx_weekly_report_user", columnList = "user_id")
)
@Getter
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class WeeklyReport extends BaseTimeEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "user_id", nullable = false)
    private User user;

    @Column(name = "week_start_date", nullable = false)
    private LocalDate weekStartDate;

    @Column(name = "week_end_date", nullable = false)
    private LocalDate weekEndDate;

    @Enumerated(EnumType.STRING)
    @Column(length = 20, nullable = false)
    private ReportStatus status;

    @Column(columnDefinition = "TEXT")
    private String weeklySummary;

    @Column(length = 50)
    private String topEmotion;

    @Column(columnDefinition = "TEXT")
    private String growthTip;

    private Integer weeklyScore;

    @Column(columnDefinition = "TEXT")
    private String errorMessage;

    public WeeklyReport(User user, LocalDate weekStartDate, LocalDate weekEndDate) {
        this.user = user;
        this.weekStartDate = weekStartDate;
        this.weekEndDate = weekEndDate;
        this.status = ReportStatus.PENDING;
    }

    public void markDone(String summary, String emotion, String tip, Integer score) {
        this.status = ReportStatus.DONE;
        this.weeklySummary = summary;
        this.topEmotion = emotion;
        this.growthTip = tip;
        this.weeklyScore = score;
        this.errorMessage = null;
    }

    public void markFailed(String reason) {
        this.status = ReportStatus.FAILED;
        this.errorMessage = reason;
    }
}
