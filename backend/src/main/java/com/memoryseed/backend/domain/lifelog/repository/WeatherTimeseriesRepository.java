package com.memoryseed.backend.domain.lifelog.repository;

import com.memoryseed.backend.domain.lifelog.entity.WeatherTimeseries;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.time.LocalDateTime;

public interface WeatherTimeseriesRepository extends JpaRepository<WeatherTimeseries, Long> {
    List<WeatherTimeseries> findByRunId(Long runId);
    List<WeatherTimeseries> findByUserIdAndTimeBetween(Long userId, LocalDateTime start, LocalDateTime end);
}
