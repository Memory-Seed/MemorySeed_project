package com.memoryseed.backend.domain.quest.controller;

import com.memoryseed.backend.domain.quest.dto.AiQuestCreateRequest;
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

    // 1. 사용자 직접 생성 API
    @PostMapping("/custom")
    public ResponseEntity<QuestResponse> createCustomQuest(
            @RequestHeader("X-USER-ID") Long userId,
            @Valid @RequestBody QuestCreateRequest request
    ) {
        QuestResponse response = questService.createCustomQuest(userId, request);
        return ResponseEntity.status(HttpStatus.CREATED).body(response);
    }

    // 2. AI 추천 퀘스트 생성 API
    @PostMapping("/ai-recommend")
    public ResponseEntity<QuestResponse> createAiQuest(
            @RequestHeader("X-USER-ID") Long userId,
            @Valid @RequestBody AiQuestCreateRequest request
    ) {
        QuestResponse response = questService.createAiQuest(userId, request);
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
