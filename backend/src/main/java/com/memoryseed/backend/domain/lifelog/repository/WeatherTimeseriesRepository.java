package com.memoryseed.backend.domain.lifelog.repository;

import com.memoryseed.backend.domain.lifelog.entity.WeatherTimeseries;
import com.memoryseed.backend.domain.user.entity.User;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.time.LocalDateTime;

public interface WeatherTimeseriesRepository extends JpaRepository<WeatherTimeseries, Long> {
    List<WeatherTimeseries> findByRunId(Long runId);
    List<WeatherTimeseries> findByUserAndTimeBetween(User user, LocalDateTime start, LocalDateTime end);
}
