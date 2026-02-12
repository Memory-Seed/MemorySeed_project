package com.memoryseed.backend.domain.lifelog.dto;

import java.time.LocalDateTime;
import java.util.List;

public record BatchUploadRequest(
        LocalDateTime runAt,
        List<StepDto> steps,
        List<SleepDto> sleeps,
        List<ScreenTimeDto> screenTimes,
        List<WeatherDto> weathers,
        List<TransactionDto> transactions
) {
    public record StepDto(LocalDateTime time, Integer stepCount) {}
    public record SleepDto(LocalDateTime startTime, LocalDateTime endTime, Integer durationMin) {}
    public record ScreenTimeDto(String appPackage, LocalDateTime startTime, LocalDateTime endTime, Integer durationSec) {}
    public record WeatherDto(LocalDateTime time, Double temperatureC, Integer pm10, String condition) {}
    public record TransactionDto(LocalDateTime timestamp, Integer amountKrw, String merchant, String rawMessage) {}
}
