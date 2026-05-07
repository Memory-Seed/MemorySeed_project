package com.memoryseed.backend.domain.quest.dto;

import com.memoryseed.backend.domain.quest.entity.QuestCategory;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

public record AiQuestCreateRequest(
        @NotNull(message = "원하는 퀘스트 카테고리를 선택해주세요.")
        QuestCategory category,

        // 일기 텍스트 (선택). AI가 내용을 분석해 맞춤형 퀘스트를 생성합니다.
        @Size(max = 2000, message = "일기 텍스트는 2000자 이내로 입력해주세요.")
        String diaryText
) {}
