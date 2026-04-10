package com.memoryseed.backend.domain.timeblock.controller;

import com.memoryseed.backend.domain.timeblock.dto.TimeBlockCreateRequest;
import com.memoryseed.backend.domain.timeblock.dto.TimeBlockResponse;
import com.memoryseed.backend.domain.timeblock.entity.TimeBlockType;
import com.memoryseed.backend.domain.timeblock.service.TimeBlockService;
import jakarta.validation.Valid;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDate;
import java.util.List;

@RestController
@RequestMapping("/api/time-blocks")
public class TimeBlockController {

    private final TimeBlockService timeBlockService;

    public TimeBlockController(TimeBlockService timeBlockService) {
        this.timeBlockService = timeBlockService;
    }

    @PostMapping
    public ResponseEntity<TimeBlockResponse> create(
            Authentication authentication,
            @Valid @RequestBody TimeBlockCreateRequest req
    ) {
        String providerId = authentication.getName();
        return ResponseEntity.ok(timeBlockService.create(providerId, req));
    }

    @GetMapping
    public ResponseEntity<List<TimeBlockResponse>> list(
            Authentication authentication,
            @RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate from,
            @RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate to,
            @RequestParam(required = false) TimeBlockType type
    ) {
        String providerId = authentication.getName();
        return ResponseEntity.ok(timeBlockService.list(providerId, from, to, type));
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<?> delete(
            Authentication authentication,
            @PathVariable Long id
    ) {
        String providerId = authentication.getName();
        timeBlockService.delete(providerId, id);
        return ResponseEntity.noContent().build();
    }
}