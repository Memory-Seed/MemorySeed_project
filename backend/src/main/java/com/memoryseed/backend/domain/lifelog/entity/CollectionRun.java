package com.memoryseed.backend.domain.lifelog.entity;

import com.memoryseed.backend.domain.user.entity.User;
import com.memoryseed.backend.global.entity.BaseTimeEntity;
import jakarta.persistence.*;

import java.time.LocalDateTime;

@Entity
@Table(
        name = "collection_runs",
        indexes = {
                @Index(name = "idx_runs_user_runAt", columnList = "user_id, runAt")
        }
)
public class CollectionRun extends BaseTimeEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    // 누구의 수집 실행인지
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id", nullable = false)
    private User user;

    // 앱에서 "수집을 실행한 시각" (서버 수신 시간이 아니라 실행 시간)
    @Column(nullable = false)
    private LocalDateTime runAt;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 10)
    private RunStatus status = RunStatus.SUCCESS;

    protected CollectionRun() { }

    public CollectionRun(User user, LocalDateTime runAt) {
        this.user = user;
        this.runAt = runAt;
        this.status = RunStatus.SUCCESS;
    }

    public Long getId() { return id; }
    public User getUser() { return user; }
    public LocalDateTime getRunAt() { return runAt; }
    public RunStatus getStatus() { return status; }

    public void markFail() {
        this.status = RunStatus.FAIL;
    }
}
