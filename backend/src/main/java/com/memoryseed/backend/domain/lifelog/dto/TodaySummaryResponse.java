package com.memoryseed.backend.domain.lifelog.dto;

import java.util.Map;

public record TodaySummaryResponse(
        Long runId,
        int totalSteps,
        int totalSleepMinutes,
        int totalScreenTimeSeconds,
        int totalTransactionAmountKrw,
        double avgTemperatureC,
        Integer avgPm10,
        Map<String, Integer> screenTimeByAppSeconds
) { }
