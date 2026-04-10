package com.memoryseed.backend.domain.lifelog.controller;

import com.memoryseed.backend.domain.lifelog.dto.LifelogRawResponse;
import com.memoryseed.backend.domain.lifelog.dto.TodaySummaryResponse;
import com.memoryseed.backend.domain.lifelog.service.LifelogQueryService;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
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
            Authentication authentication,
            @RequestParam(required = false) LocalDate date
    ) {
        String providerId = authentication.getName();
        LocalDate target = (date == null) ? LocalDate.now() : date;

        return lifelogQueryService.getTodaySummary(providerId, target)
                .<ResponseEntity<?>>map(ResponseEntity::ok)
                .orElseGet(() -> ResponseEntity.noContent().build());
    }

    @GetMapping("/raw")
    public ResponseEntity<LifelogRawResponse> getRawLifelogs(
            Authentication authentication,
            @RequestParam("startDate") LocalDate startDate,
            @RequestParam("endDate") LocalDate endDate
    ) {
        String providerId = authentication.getName();
        LifelogRawResponse response = lifelogQueryService.getRawLifelogs(providerId, startDate, endDate);
        return ResponseEntity.ok(response);
    }
}

