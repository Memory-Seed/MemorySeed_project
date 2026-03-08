package com.memoryseed.backend.domain.quest.controller;

import com.memoryseed.backend.domain.quest.dto.QuestCreateRequest;
import com.memoryseed.backend.domain.quest.dto.QuestResponse;
import com.memoryseed.backend.domain.quest.service.QuestService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/quests")
@RequiredArgsConstructor
public class QuestController {

    private final QuestService questService;

    @PostMapping
    public ResponseEntity<QuestResponse> createQuest(
            @RequestHeader("X-USER-ID") Long userId,
            @Valid @RequestBody QuestCreateRequest request
    ) {
        QuestResponse response = questService.createQuest(userId, request);
        return ResponseEntity.status(HttpStatus.CREATED).body(response);
    }

    @GetMapping("/active")
    public ResponseEntity<List<QuestResponse>> getActiveQuests(
            @RequestHeader("X-USER-ID") Long userId
    ) {
        List<QuestResponse> activeQuests = questService.getActiveQuests(userId);
        return ResponseEntity.ok(activeQuests);
    }

    @PatchMapping("/{questId}/complete")
    public ResponseEntity<QuestResponse> completeQuest(
            @RequestHeader("X-USER-ID") Long userId,
            @PathVariable Long questId
    ) {
        QuestResponse response = questService.completeQuest(userId, questId);
        return ResponseEntity.ok(response);
    }
}
