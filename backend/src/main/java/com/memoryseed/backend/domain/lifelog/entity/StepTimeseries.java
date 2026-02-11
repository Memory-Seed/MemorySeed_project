package com.memoryseed.backend.domain.lifelog.entity;

import com.memoryseed.backend.domain.user.entity.User;
import com.memoryseed.backend.global.entity.BaseTimeEntity;
import jakarta.persistence.*;

import java.time.LocalDateTime;

@Entity
@Table(
        name = "step_timeseries",
        indexes = {
                @Index(name = "idx_step_user_time", columnList = "user_id, time")
        }
)
public class StepTimeseries extends BaseTimeEntity {

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
    private LocalDateTime time;

    @Column(nullable = false)
    private Integer stepCount;

    protected StepTimeseries() {}

    public StepTimeseries(User user, CollectionRun run, LocalDateTime time, Integer stepCount) {
        this.user = user;
        this.run = run;
        this.time = time;
        this.stepCount = stepCount;
    }

    public Long getId() { return id; }
    public User getUser() { return user; }
    public CollectionRun getRun() { return run; }
    public LocalDateTime getTime() { return time; }
    public Integer getStepCount() { return stepCount; }
}
