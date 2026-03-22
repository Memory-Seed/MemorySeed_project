package com.memoryseed.backend.domain.lifelog.controller;

import com.memoryseed.backend.domain.lifelog.dto.LifelogRawResponse;
import com.memoryseed.backend.domain.lifelog.dto.TodaySummaryResponse;
import com.memoryseed.backend.domain.lifelog.service.LifelogQueryService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDate;

@RestController
@RequestMapping("/api/lifelog")
public class LifelogQueryController {

    private final LifelogQueryService lifelogQueryService;

    public LifelogQueryController(LifelogQueryService lifelogQueryService) {
        this.lifelogQueryService = lifelogQueryService;
    }

    @GetMapping("/today")
    public ResponseEntity<?> getToday(
            @RequestHeader("X-USER-ID") Long userId,
            @RequestParam(required = false) LocalDate date
    ) {
        LocalDate target = (date == null) ? LocalDate.now() : date;

        return lifelogQueryService.getTodaySummary(userId, target)
                .<ResponseEntity<?>>map(ResponseEntity::ok)
                .orElseGet(() -> ResponseEntity.noContent().build());
    }

    @GetMapping("/raw")
    public ResponseEntity<LifelogRawResponse> getRawLifelogs(
            @RequestHeader("X-USER-ID") Long userId,
            @RequestParam("startDate") LocalDate startDate,
            @RequestParam("endDate") LocalDate endDate
    ) {
        LifelogRawResponse response = lifelogQueryService.getRawLifelogs(userId, startDate, endDate);
        return ResponseEntity.ok(response);
    }
}

