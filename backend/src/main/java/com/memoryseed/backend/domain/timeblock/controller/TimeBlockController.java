package com.memoryseed.backend.domain.timeblock.controller;

import com.memoryseed.backend.domain.timeblock.dto.TimeBlockCreateRequest;
import com.memoryseed.backend.domain.timeblock.dto.TimeBlockResponse;
import com.memoryseed.backend.domain.timeblock.entity.TimeBlockType;
import com.memoryseed.backend.domain.timeblock.service.TimeBlockService;
import jakarta.validation.Valid;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.http.ResponseEntity;
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
            @RequestHeader("X-USER-ID") Long userId,
            @Valid @RequestBody TimeBlockCreateRequest req
    ) {
        return ResponseEntity.ok(timeBlockService.create(userId, req));
    }

    @GetMapping
    public ResponseEntity<List<TimeBlockResponse>> list(
            @RequestHeader("X-USER-ID") Long userId,
            @RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate from,
            @RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate to,
            @RequestParam(required = false) TimeBlockType type
    ) {
        return ResponseEntity.ok(timeBlockService.list(userId, from, to, type));
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<?> delete(
            @RequestHeader("X-USER-ID") Long userId,
            @PathVariable Long id
    ) {
        timeBlockService.delete(userId, id);
        return ResponseEntity.noContent().build();
    }
}