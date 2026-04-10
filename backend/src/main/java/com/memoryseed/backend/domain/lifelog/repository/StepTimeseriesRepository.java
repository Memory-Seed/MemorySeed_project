package com.memoryseed.backend.domain.lifelog.repository;

import com.memoryseed.backend.domain.lifelog.entity.StepTimeseries;
import com.memoryseed.backend.domain.user.entity.User;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.time.LocalDateTime;

public interface StepTimeseriesRepository extends JpaRepository<StepTimeseries, Long> {
    List<StepTimeseries> findByRunId(Long runId);
    List<StepTimeseries> findByUserAndTimeBetween(User user, LocalDateTime start, LocalDateTime end);
}
