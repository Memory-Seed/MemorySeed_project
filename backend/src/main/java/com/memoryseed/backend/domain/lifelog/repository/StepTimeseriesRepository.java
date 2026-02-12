package com.memoryseed.backend.domain.lifelog.repository;

import com.memoryseed.backend.domain.lifelog.entity.StepTimeseries;
import org.springframework.data.jpa.repository.JpaRepository;

public interface StepTimeseriesRepository extends JpaRepository<StepTimeseries, Long> { }
