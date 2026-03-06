package com.memoryseed.backend.domain.lifelog.service;

import com.memoryseed.backend.domain.lifelog.dto.BatchUploadRequest;
import com.memoryseed.backend.domain.lifelog.entity.*;
import com.memoryseed.backend.domain.lifelog.repository.*;
import com.memoryseed.backend.domain.user.entity.User;
import com.memoryseed.backend.domain.user.repository.UserRepository;
import lombok.RequiredArgsConstructor; // Lombok의 RequiredArgsConstructor 사용
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.time.ZoneId;
import java.time.LocalDateTime;

@Slf4j // Lombok의 Slf4j 사용
@Service
@RequiredArgsConstructor // 생성자 주입을 Lombok으로 처리
public class LifelogBatchService {

    private final UserRepository userRepository;
    private final CollectionRunRepository runRepository;
    private final StepTimeseriesRepository stepRepository;
    private final SleepSessionRepository sleepRepository;
    private final ScreenTimeSessionRepository screenRepository;
    private final WeatherTimeseriesRepository weatherRepository;
    private final TransactionEventRepository txRepository;

    private final WeatherIngestService weatherIngestService;

    @Transactional
    public Long upload(Long userId, BatchUploadRequest req) {
        User user = userRepository.findById(userId)
                .orElseThrow(() -> new IllegalArgumentException("user not found: " + userId));

        // 서버가 기본 runAt을 결정 (클라 값 믿지 말기)
        LocalDateTime runAt = (req.runAt() != null)
                ? req.runAt()
                : LocalDateTime.now(ZoneId.of("Asia/Seoul"));

        // 1) run 생성
        CollectionRun run = CollectionRun.builder()
                .user(user)
                .runAt(runAt)
                .status(RunStatus.SUCCESS)
                .build();
        runRepository.save(run);

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
                    .map(t -> new TransactionEvent(
                            user,
                            run,
                            t.timestamp(),
                            t.amountKrw(),
                            t.merchant(),
                            t.rawMessage()
                    ))
                    .toList();

            txRepository.saveAll(txs);
        }

        if (req.location() != null) { // 날씨 정보는 location이 있을 때만 시도
            try {
                weatherIngestService.fetchAndSaveWeather(user, run, req.location());
            } catch (Exception e) {
                // 날씨 저장이 실패해도 메인 데이터(Run) 저장은 성공해야 함 -> 로그만 남김
                log.error("Batch upload 중 날씨 저장 실패: {}", e.getMessage());
            }
        }

        return run.getId();
    }
}
