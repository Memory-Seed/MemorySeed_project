package com.memoryseed.backend.domain.timeblock.entity;

import com.memoryseed.backend.domain.user.entity.User;
import com.memoryseed.backend.global.entity.BaseTimeEntity;
import jakarta.persistence.*;
import lombok.AccessLevel;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;
import java.time.temporal.ChronoUnit;

@Entity
@Table(
        name = "time_blocks",
        indexes = {
                @Index(name = "idx_timeblock_user_start", columnList = "user_id,start_time")
        }
)
@Getter
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class TimeBlock extends BaseTimeEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name="user_id", nullable = false)
    private User user;

    @Column(name="start_time", nullable = false)
    private LocalDateTime startTime;

    @Column(name="end_time", nullable = false)
    private LocalDateTime endTime;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 10)
    private TimeBlockType type;

    @Column(name="duration_min", nullable = false)
    private Integer durationMin;

    public TimeBlock(User user, LocalDateTime startTime, LocalDateTime endTime, TimeBlockType type) {
        if (startTime == null || endTime == null || type == null) {
            throw new IllegalArgumentException("startTime/endTime/type must not be null");
        }
        if (!endTime.isAfter(startTime)) {
            throw new IllegalArgumentException("endTime must be after startTime");
        }
        this.user = user;
        this.startTime = startTime;
        this.endTime = endTime;
        this.type = type;
        this.durationMin = (int) ChronoUnit.MINUTES.between(startTime, endTime);
    }

    public void update(LocalDateTime startTime, LocalDateTime endTime, TimeBlockType type) {
        if (startTime == null || endTime == null || type == null) {
            throw new IllegalArgumentException("startTime/endTime/type must not be null");
        }
        if (!endTime.isAfter(startTime)) {
            throw new IllegalArgumentException("endTime must be after startTime");
        }
        this.startTime = startTime;
        this.endTime = endTime;
        this.type = type;
        this.durationMin = (int) ChronoUnit.MINUTES.between(startTime, endTime);
    }
}