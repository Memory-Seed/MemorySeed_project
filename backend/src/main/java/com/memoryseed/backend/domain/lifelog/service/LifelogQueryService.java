package com.memoryseed.backend.domain.lifelog.service;

import com.memoryseed.backend.domain.lifelog.dto.LifelogRawResponse;
import com.memoryseed.backend.domain.lifelog.dto.TodaySummaryResponse;
import com.memoryseed.backend.domain.lifelog.entity.CollectionRun;
import com.memoryseed.backend.domain.lifelog.repository.*;
import com.memoryseed.backend.domain.user.entity.User;
import com.memoryseed.backend.domain.user.repository.UserRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.stream.Collectors;

@Service
public class LifelogQueryService {

    private final UserRepository userRepository;
    private final CollectionRunRepository runRepository;
    private final StepTimeseriesRepository stepRepository;
    private final SleepSessionRepository sleepRepository;
    private final ScreenTimeSessionRepository screenRepository;
    private final WeatherTimeseriesRepository weatherRepository;
    private final TransactionEventRepository txRepository;

    public LifelogQueryService(
            UserRepository userRepository,
            CollectionRunRepository runRepository,
            StepTimeseriesRepository stepRepository,
            SleepSessionRepository sleepRepository,
            ScreenTimeSessionRepository screenRepository,
            WeatherTimeseriesRepository weatherRepository,
            TransactionEventRepository txRepository
    ) {
        this.userRepository = userRepository;
        this.runRepository = runRepository;
        this.stepRepository = stepRepository;
        this.sleepRepository = sleepRepository;
        this.screenRepository = screenRepository;
        this.weatherRepository = weatherRepository;
        this.txRepository = txRepository;
    }

    @Transactional(readOnly = true)
    public Optional<TodaySummaryResponse> getTodaySummary(String providerId, LocalDate date) {
        User user = userRepository.findByProviderId(providerId)
                .orElseThrow(() -> new IllegalArgumentException("User not found with providerId: " + providerId));

        LocalDateTime start = date.atStartOfDay();
        LocalDateTime end = date.plusDays(1).atStartOfDay();

        Optional<CollectionRun> latestRunOpt =
                runRepository.findTopByUserAndRunAtBetweenOrderByRunAtDesc(user, start, end);

        if (latestRunOpt.isEmpty()) return Optional.empty();

        Long runId = latestRunOpt.get().getId();

        int totalSteps = stepRepository.findByRunId(runId).stream()
                .mapToInt(s -> s.getStepCount() == null ? 0 : s.getStepCount())
                .sum();

        int totalSleepMin = sleepRepository.findByRunId(runId).stream()
                .mapToInt(s -> s.getDurationMin() == null ? 0 : s.getDurationMin())
                .sum();

        var screenList = screenRepository.findByRunId(runId);
        int totalScreenSec = screenList.stream()
                .mapToInt(s -> s.getDurationSec() == null ? 0 : s.getDurationSec())
                .sum();

        Map<String, Integer> screenByApp = screenList.stream()
                .collect(Collectors.groupingBy(
                        s -> s.getAppPackage(),
                        Collectors.summingInt(s -> s.getDurationSec() == null ? 0 : s.getDurationSec())
                ));

        int totalTxKrw = txRepository.findByRunId(runId).stream()
                .mapToInt(t -> t.getAmountKrw() == null ? 0 : t.getAmountKrw())
                .sum();

        var weathers = weatherRepository.findByRunId(runId);

        double avgTemp = weathers.isEmpty() ? 0.0 :
                weathers.stream().mapToDouble(w -> w.getTemperatureC() == null ? 0.0 : w.getTemperatureC()).average().orElse(0.0);

        Integer avgPm10 = weathers.isEmpty() ? null :
                (int) Math.round(weathers.stream().filter(w -> w.getPm10() != null).mapToInt(w -> w.getPm10()).average().orElse(Double.NaN));

        return Optional.of(new TodaySummaryResponse(
                runId,
                totalSteps,
                totalSleepMin,
                totalScreenSec,
                totalTxKrw,
                avgTemp,
                avgPm10,
                screenByApp
        ));
    }

    @Transactional(readOnly = true)
    public LifelogRawResponse getRawLifelogs(String providerId, LocalDate startDate, LocalDate endDate) {
        User user = userRepository.findByProviderId(providerId)
                .orElseThrow(() -> new IllegalArgumentException("User not found with providerId: " + providerId));

        LocalDateTime startDateTime = startDate.atStartOfDay();
        LocalDateTime endDateTime = endDate.atTime(23, 59, 59);

        List<LifelogRawResponse.TransactionEventDto> transactionEvents = txRepository.findByUserAndTimestampBetween(user, startDateTime, endDateTime)
                .stream()
                .map(LifelogRawResponse.TransactionEventDto::from)
                .toList();

        List<LifelogRawResponse.ScreenTimeSessionDto> screenTimeSessions = screenRepository.findByUserAndStartTimeBetween(user, startDateTime, endDateTime)
                .stream()
                .map(LifelogRawResponse.ScreenTimeSessionDto::from)
                .toList();

        List<LifelogRawResponse.SleepSessionDto> sleepSessions = sleepRepository.findByUserAndStartTimeBetween(user, startDateTime, endDateTime)
                .stream()
                .map(LifelogRawResponse.SleepSessionDto::from)
                .toList();

        List<LifelogRawResponse.StepTimeseriesDto> stepTimeseries = stepRepository.findByUserAndTimeBetween(user, startDateTime, endDateTime)
                .stream()
                .map(LifelogRawResponse.StepTimeseriesDto::from)
                .toList();

        List<LifelogRawResponse.WeatherTimeseriesDto> weatherTimeseries = weatherRepository.findByUserAndTimeBetween(user, startDateTime, endDateTime)
                .stream()
                .map(LifelogRawResponse.WeatherTimeseriesDto::from)
                .toList();

        return new LifelogRawResponse(
                transactionEvents,
                screenTimeSessions,
                sleepSessions,
                stepTimeseries,
                weatherTimeseries
        );
    }
}
