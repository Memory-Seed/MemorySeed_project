package com.memoryseed.backend.domain.lifelog.dto;

import com.memoryseed.backend.domain.lifelog.entity.ScreenTimeSession;
import com.memoryseed.backend.domain.lifelog.entity.SleepSession;
import com.memoryseed.backend.domain.lifelog.entity.StepTimeseries;
import com.memoryseed.backend.domain.lifelog.entity.TransactionEvent;
import com.memoryseed.backend.domain.lifelog.entity.WeatherTimeseries;

import java.time.LocalDateTime;
import java.util.List;

public record LifelogRawResponse(
        List<TransactionEventDto> transactions,
        List<ScreenTimeSessionDto> screenTimes,
        List<SleepSessionDto> sleeps,
        List<StepTimeseriesDto> steps,
        List<WeatherTimeseriesDto> weathers
) {
    public record TransactionEventDto(
            Long id,
            Long runId,
            LocalDateTime timestamp,
            Integer amountKrw,
            String merchant
    ) {
        public static TransactionEventDto from(TransactionEvent entity) {
            return new TransactionEventDto(
                    entity.getId(),
                    entity.getRun().getId(),
                    entity.getTimestamp(),
                    entity.getAmountKrw(),
                    entity.getMerchant()
            );
        }
    }

    public record ScreenTimeSessionDto(
            Long id,
            Long runId,
            String appPackage,
            LocalDateTime startTime,
            LocalDateTime endTime,
            Integer durationSec
    ) {
        public static ScreenTimeSessionDto from(ScreenTimeSession entity) {
            return new ScreenTimeSessionDto(
                    entity.getId(),
                    entity.getRun().getId(),
                    entity.getAppPackage(),
                    entity.getStartTime(),
                    entity.getEndTime(),
                    entity.getDurationSec()
            );
        }
    }

    public record SleepSessionDto(
            Long id,
            Long runId,
            LocalDateTime startTime,
            LocalDateTime endTime,
            Integer durationMin
    ) {
        public static SleepSessionDto from(SleepSession entity) {
            return new SleepSessionDto(
                    entity.getId(),
                    entity.getRun().getId(),
                    entity.getStartTime(),
                    entity.getEndTime(),
                    entity.getDurationMin()
            );
        }
    }

    public record StepTimeseriesDto(
            Long id,
            Long runId,
            LocalDateTime time,
            Integer stepCount
    ) {
        public static StepTimeseriesDto from(StepTimeseries entity) {
            return new StepTimeseriesDto(
                    entity.getId(),
                    entity.getRun().getId(),
                    entity.getTime(),
                    entity.getStepCount()
            );
        }
    }

    public record WeatherTimeseriesDto(
            Long id,
            Long runId,
            LocalDateTime time,
            Double temperatureC,
            Integer pm10,
            String condition
    ) {
        public static WeatherTimeseriesDto from(WeatherTimeseries entity) {
            return new WeatherTimeseriesDto(
                    entity.getId(),
                    entity.getRun().getId(),
                    entity.getTime(),
                    entity.getTemperatureC(),
                    entity.getPm10(),
                    entity.getCondition()
            );
        }
    }
}
