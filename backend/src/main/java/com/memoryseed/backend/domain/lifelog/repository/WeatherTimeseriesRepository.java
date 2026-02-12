package com.memoryseed.backend.domain.lifelog.repository;

import com.memoryseed.backend.domain.lifelog.entity.WeatherTimeseries;
import org.springframework.data.jpa.repository.JpaRepository;

public interface WeatherTimeseriesRepository extends JpaRepository<WeatherTimeseries, Long> { }
