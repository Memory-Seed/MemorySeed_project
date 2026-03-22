package com.memoryseed.backend.domain.lifelog.repository;

import com.memoryseed.backend.domain.lifelog.entity.ScreenTimeSession;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.time.LocalDateTime;

public interface ScreenTimeSessionRepository extends JpaRepository<ScreenTimeSession, Long> {
    List<ScreenTimeSession> findByRunId(Long runId);
    List<ScreenTimeSession> findByUserIdAndStartTimeBetween(Long userId, LocalDateTime start, LocalDateTime end);
}
