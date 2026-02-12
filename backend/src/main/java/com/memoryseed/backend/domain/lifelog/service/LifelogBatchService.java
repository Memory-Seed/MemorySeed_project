package com.memoryseed.backend.domain.lifelog.service;

import com.memoryseed.backend.domain.lifelog.dto.BatchUploadRequest;
import com.memoryseed.backend.domain.lifelog.entity.*;
import com.memoryseed.backend.domain.lifelog.repository.*;
import com.memoryseed.backend.domain.user.entity.User;
import com.memoryseed.backend.domain.user.repository.UserRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Service
public class LifelogBatchService {

    private final UserRepository userRepository;
    private final CollectionRunRepository runRepository;
    private final StepTimeseriesRepository stepRepository;
    private final SleepSessionRepository sleepRepository;
    private final ScreenTimeSessionRepository screenRepository;
    private final WeatherTimeseriesRepository weatherRepository;
    private final TransactionEventRepository txRepository;

    public LifelogBatchService(
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

    @Transactional
    public Long upload(Long userId, BatchUploadRequest req) {
        User user = userRepository.findById(userId)
                .orElseThrow(() -> new IllegalArgumentException("user not found: " + userId));

        // 1) run 생성
        CollectionRun run = runRepository.save(new CollectionRun(user, req.runAt()));

        // 2) 각 데이터 저장 (null 안전 처리)
        if (req.steps() != null && !req.steps().isEmpty()) {
            List<StepTimeseries> steps = req.steps().stream()
                    .map(s -> new StepTimeseries(user, run, s.time(), s.stepCount()))
                    .toList();
            stepRepository.saveAll(steps);
        }

        if (req.sleeps() != null && !req.sleeps().isEmpty()) {
            List<SleepSession> sleeps = req.sleeps().stream()
                    .map(s -> new SleepSession(user, run, s.startTime(), s.endTime(), s.durationMin()))
                    .toList();
            sleepRepository.saveAll(sleeps);
        }

        if (req.screenTimes() != null && !req.screenTimes().isEmpty()) {
            List<ScreenTimeSession> screens = req.screenTimes().stream()
                    .map(s -> new ScreenTimeSession(user, run, s.appPackage(), s.startTime(), s.endTime(), s.durationSec()))
                    .toList();
            screenRepository.saveAll(screens);
        }

        if (req.weathers() != null && !req.weathers().isEmpty()) {
            List<WeatherTimeseries> weathers = req.weathers().stream()
                    .map(w -> new WeatherTimeseries(user, run, w.time(), w.temperatureC(), w.pm10(), w.condition()))
                    .toList();
            weatherRepository.saveAll(weathers);
        }

        if (req.transactions() != null && !req.transactions().isEmpty()) {
            List<TransactionEvent> txs = req.transactions().stream()
                    .map(t -> new TransactionEvent(user, run, t.timestamp(), t.amountKrw(), t.merchant(), t.rawMessage()))
                    .toList();
            txRepository.saveAll(txs);
        }

        return run.getId();
    }
}
