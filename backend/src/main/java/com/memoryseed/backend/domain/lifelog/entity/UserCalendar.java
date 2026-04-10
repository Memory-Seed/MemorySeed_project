package com.memoryseed.backend.domain.lifelog.entity;

import com.memoryseed.backend.domain.user.entity.User;
import jakarta.persistence.*;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

@Entity
@Table(name = "user_calendars")
@Getter
@NoArgsConstructor
public class UserCalendar {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id", nullable = false)
    private User user;

    @Column(name = "google_event_id")
    private String googleEventId;

    private String summary;

    @Column(name = "start_time")
    private LocalDateTime startTime;

    @Column(name = "end_time")
    private LocalDateTime endTime;

    private String status;

    @Builder
    public UserCalendar(User user, String googleEventId, String summary,
                        LocalDateTime startTime, LocalDateTime endTime, String status) {
        this.user = user;
        this.googleEventId = googleEventId;
        this.summary = summary;
        this.startTime = startTime;
        this.endTime = endTime;
        this.status = status;
    }
}