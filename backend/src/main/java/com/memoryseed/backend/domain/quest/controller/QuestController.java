package com.memoryseed.backend.domain.quest.controller;

import com.memoryseed.backend.domain.quest.dto.AiQuestCreateRequest;
import com.memoryseed.backend.domain.quest.dto.QuestCreateRequest;
import com.memoryseed.backend.domain.quest.dto.QuestResponse;
import com.memoryseed.backend.domain.quest.service.QuestService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/quests")
@RequiredArgsConstructor
public class QuestController {

    private final QuestService questService;

    // 1. 사용자 직접 생성 API
    @PostMapping("/custom")
    public ResponseEntity<QuestResponse> createCustomQuest(
            Authentication authentication,
            @Valid @RequestBody QuestCreateRequest request
    ) {
        String providerId = authentication.getName();
        QuestResponse response = questService.createCustomQuest(providerId, request);
        return ResponseEntity.status(HttpStatus.CREATED).body(response);
    }

    // 2. AI 추천 퀘스트 생성 API (여러 개 반환)
    @PostMapping("/ai-recommend")
    public ResponseEntity<List<QuestResponse>> createAiQuests(
            Authentication authentication,
            @Valid @RequestBody AiQuestCreateRequest request
    ) {
        String providerId = authentication.getName();
        List<QuestResponse> response = questService.createAiQuests(providerId, request);
        return ResponseEntity.status(HttpStatus.CREATED).body(response);
    }

    @GetMapping("/active")
    public ResponseEntity<List<QuestResponse>> getActiveQuests(
            Authentication authentication
    ) {
        String providerId = authentication.getName();
        List<QuestResponse> activeQuests = questService.getActiveQuests(providerId);
        return ResponseEntity.ok(activeQuests);
    }

    @PatchMapping("/{questId}/complete")
    public ResponseEntity<QuestResponse> completeQuest(
            Authentication authentication,
            @PathVariable Long questId
    ) {
        String providerId = authentication.getName();
        QuestResponse response = questService.completeQuest(providerId, questId);
        return ResponseEntity.ok(response);
    }

    @DeleteMapping("/{questId}")
    public ResponseEntity<Void> deleteQuest(
            Authentication authentication,
            @PathVariable Long questId
    ) {
        String providerId = authentication.getName();
        questService.deleteQuest(providerId, questId);
        return ResponseEntity.noContent().build();
    }
}
