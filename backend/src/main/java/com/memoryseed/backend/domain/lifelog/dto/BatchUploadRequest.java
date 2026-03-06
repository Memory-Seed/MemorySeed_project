package com.memoryseed.backend.domain.lifelog.dto;

import jakarta.validation.Valid;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotNull;


import java.time.LocalDateTime;
import java.util.List;

public record BatchUploadRequest(
        @NotNull(message = "runAt은 필수입니다.")
        LocalDateTime runAt,

        @Valid
        @NotNull(message = "location은 필수입니다.")
        LocationDto location,

        @Valid List<StepDto> steps,
        @Valid List<SleepDto> sleeps,
        @Valid List<ScreenTimeDto> screenTimes,
        @Valid List<WeatherDto> weathers,
        @Valid List<TransactionDto> transactions
) {

    public record StepDto(
            @NotNull(message = "steps.time은 필수입니다.")
            LocalDateTime time,

            @NotNull(message = "steps.stepCount는 필수입니다.")
            @jakarta.validation.constraints.PositiveOrZero(message = "steps.stepCount는 0 이상이어야 합니다.")
            Integer stepCount
    ) {}

    public record SleepDto(
            @NotNull(message = "sleeps.startTime은 필수입니다.")
            LocalDateTime startTime,

            @NotNull(message = "sleeps.endTime은 필수입니다.")
            LocalDateTime endTime,

            @jakarta.validation.constraints.PositiveOrZero(message = "sleeps.durationMin은 0 이상이어야 합니다.")
            Integer durationMin
    ) {}

    public record ScreenTimeDto(
            @jakarta.validation.constraints.NotBlank(message = "screenTimes.appPackage는 필수입니다.")
            String appPackage,

            @NotNull(message = "screenTimes.startTime은 필수입니다.")
            LocalDateTime startTime,

            @NotNull(message = "screenTimes.endTime은 필수입니다.")
            LocalDateTime endTime,

            @jakarta.validation.constraints.PositiveOrZero(message = "screenTimes.durationSec은 0 이상이어야 합니다.")
            Integer durationSec
    ) {}

    public record WeatherDto(
            @NotNull(message = "weathers.time은 필수입니다.")
            LocalDateTime time,

            Double temperatureC,
            Integer pm10,
            String condition
    ) {}

    public record TransactionDto(
            @NotNull(message = "transactions.timestamp는 필수입니다.")
            LocalDateTime timestamp,

            @NotNull(message = "transactions.amountKrw는 필수입니다.")
            @jakarta.validation.constraints.PositiveOrZero(message = "transactions.amountKrw는 0 이상이어야 합니다.")
            Integer amountKrw,

            String merchant,
            String rawMessage
    ) {}

}
