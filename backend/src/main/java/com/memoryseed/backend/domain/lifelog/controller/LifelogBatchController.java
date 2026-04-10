package com.memoryseed.backend.domain.lifelog.controller;

import com.memoryseed.backend.domain.lifelog.dto.BatchUploadRequest;
import com.memoryseed.backend.domain.lifelog.service.LifelogBatchService;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/lifelog")
public class LifelogBatchController {

    private final LifelogBatchService lifelogBatchService;

    public LifelogBatchController(LifelogBatchService lifelogBatchService) {
        this.lifelogBatchService = lifelogBatchService;
    }

    @PostMapping("/batch")
    public ResponseEntity<?> upload(
            Authentication authentication,
            @Valid @RequestBody BatchUploadRequest req
    ) {
        String providerId = authentication.getName();
        Long runId = lifelogBatchService.upload(providerId, req);
        return ResponseEntity.ok(Map.of("runId", runId));
    }
}
