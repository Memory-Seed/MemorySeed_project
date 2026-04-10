package com.memoryseed.backend.domain.quest.dto;

import com.memoryseed.backend.domain.quest.entity.QuestCategory;
import jakarta.validation.constraints.NotNull;

public record AiQuestCreateRequest(
        @NotNull(message = "원하는 퀘스트 카테고리를 선택해주세요.")
        QuestCategory category
        // AI에게 넘길 추가 단서(예: 난이도, 현재 기분 등)가 있다면 여기에 추가
) {
}