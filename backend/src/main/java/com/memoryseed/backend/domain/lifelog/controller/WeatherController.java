package com.memoryseed.backend.domain.lifelog.controller;

import com.memoryseed.backend.domain.lifelog.dto.LocationDto;
import com.memoryseed.backend.domain.lifelog.dto.WeatherResponseDto;
import com.memoryseed.backend.domain.lifelog.entity.CollectionRun;
import com.memoryseed.backend.domain.lifelog.repository.CollectionRunRepository;
import com.memoryseed.backend.domain.lifelog.service.WeatherIngestService;
import com.memoryseed.backend.domain.user.entity.User;
import com.memoryseed.backend.domain.user.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.time.ZoneId;

@RestController
@RequestMapping("/api/lifelog/weather")
@RequiredArgsConstructor
public class WeatherController {

    private final WeatherIngestService weatherIngestService;
    private final UserRepository userRepository;
    private final CollectionRunRepository runRepository;

    // 테스트/아침 조회용:
    // GET /api/lifelog/weather/current?lat=37.5&lon=127.0
    @GetMapping("/current")
    public ResponseEntity<WeatherResponseDto> getCurrentWeather(
            @RequestHeader("X-USER-ID") Long userId,
            @RequestParam Double lat,
            @RequestParam Double lon
    ) {
        User user = userRepository.findById(userId)
                .orElseThrow(() -> new IllegalArgumentException("User not found: " + userId));

        // run을 생성해서 weather 저장을 안정화
        LocalDateTime runAt = LocalDateTime.now(ZoneId.of("Asia/Seoul"));
        CollectionRun run = runRepository.save(new CollectionRun(user, runAt));

        LocationDto location = new LocationDto(lat, lon);

        WeatherResponseDto response = weatherIngestService.fetchAndSaveWeather(user, run, location);

        if (response == null) return ResponseEntity.noContent().build();
        return ResponseEntity.ok(response);
    }
}