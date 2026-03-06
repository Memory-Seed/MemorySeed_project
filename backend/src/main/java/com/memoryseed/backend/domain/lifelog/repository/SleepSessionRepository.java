package com.memoryseed.backend.domain.lifelog.repository;

import com.memoryseed.backend.domain.lifelog.entity.SleepSession;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface SleepSessionRepository extends JpaRepository<SleepSession, Long> {
    List<SleepSession> findByRunId(Long runId);
}
