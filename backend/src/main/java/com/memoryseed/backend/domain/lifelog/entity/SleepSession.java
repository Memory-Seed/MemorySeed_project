package com.memoryseed.backend.domain.lifelog.entity;

import com.memoryseed.backend.domain.user.entity.User;
import com.memoryseed.backend.global.entity.BaseTimeEntity;
import jakarta.persistence.*;

import java.time.LocalDateTime;

@Entity
@Table(
        name = "sleep_sessions",
        indexes = {
                @Index(name="idx_sleep_user_start", columnList="user_id, startTime")
        }
)
public class SleepSession extends BaseTimeEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name="user_id", nullable = false)
    private User user;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name="run_id", nullable = false)
    private CollectionRun run;

    @Column(nullable = false)
    private LocalDateTime startTime;

    @Column(nullable = false)
    private LocalDateTime endTime;

    @Column(nullable = false)
    private Integer durationMin;

    protected SleepSession() {}

    public SleepSession(User user, CollectionRun run, LocalDateTime startTime, LocalDateTime endTime, Integer durationMin) {
        this.user = user;
        this.run = run;
        this.startTime = startTime;
        this.endTime = endTime;
        this.durationMin = durationMin;
    }

    public Long getId() { return id; }
    public User getUser() { return user; }
    public CollectionRun getRun() { return run; }
    public LocalDateTime getStartTime() { return startTime; }
    public LocalDateTime getEndTime() { return endTime; }
    public Integer getDurationMin() { return durationMin; }
}
