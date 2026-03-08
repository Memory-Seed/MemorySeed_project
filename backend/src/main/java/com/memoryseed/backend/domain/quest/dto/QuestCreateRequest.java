package com.memoryseed.backend.domain.quest.dto;

import com.memoryseed.backend.domain.quest.entity.QuestCategory;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

public record QuestCreateRequest(
        @NotBlank(message = "퀘스트 제목은 필수입니다.")
        @Size(max = 100, message = "퀘스트 제목은 100자를 초과할 수 없습니다.")
        String title,

        @Size(max = 255, message = "퀘스트 설명은 255자를 초과할 수 없습니다.")
        String description,

        @NotNull(message = "카테고리는 필수입니다.")
        QuestCategory category
) {
}
