package com.memoryseed.backend.domain.lifelog.entity;

import com.memoryseed.backend.domain.user.entity.User;
import com.memoryseed.backend.global.entity.BaseTimeEntity;
import jakarta.persistence.*;

import java.time.LocalDateTime;

@Entity
@Table(
        name = "screen_time_sessions",
        indexes = {
                @Index(name="idx_screen_user_app", columnList="user_id, appPackage")
        }
)
public class ScreenTimeSession extends BaseTimeEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name="user_id", nullable = false)
    private User user;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name="run_id", nullable = false)
    private CollectionRun run;

    @Column(nullable = false, length = 200)
    private String appPackage;

    @Column(nullable = false)
    private LocalDateTime startTime;

    @Column(nullable = false)
    private LocalDateTime endTime;

    @Column(nullable = false)
    private Integer durationSec;

    protected ScreenTimeSession() {}

    public ScreenTimeSession(User user, CollectionRun run, String appPackage,
                             LocalDateTime startTime, LocalDateTime endTime, Integer durationSec) {
        this.user = user;
        this.run = run;
        this.appPackage = appPackage;
        this.startTime = startTime;
        this.endTime = endTime;
        this.durationSec = durationSec;
    }

    public Long getId() { return id; }
    public User getUser() { return user; }
    public CollectionRun getRun() { return run; }
    public String getAppPackage() { return appPackage; }
    public LocalDateTime getStartTime() { return startTime; }
    public LocalDateTime getEndTime() { return endTime; }
    public Integer getDurationSec() { return durationSec; }
}
