package com.memoryseed.backend.domain.lifelog.repository;

import com.memoryseed.backend.domain.lifelog.entity.SleepSession;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.time.LocalDateTime;

public interface SleepSessionRepository extends JpaRepository<SleepSession, Long> {
    List<SleepSession> findByRunId(Long runId);
    List<SleepSession> findByUserIdAndStartTimeBetween(Long userId, LocalDateTime start, LocalDateTime end);
}
