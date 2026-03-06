package com.memoryseed.backend.domain.timeblock.dto;

import com.memoryseed.backend.domain.timeblock.entity.TimeBlockType;
import jakarta.validation.constraints.NotNull;

import java.time.LocalDateTime;

public record TimeBlockCreateRequest(
        @NotNull(message="startTime은 필수입니다.")
        LocalDateTime startTime,

        @NotNull(message="endTime은 필수입니다.")
        LocalDateTime endTime,

        @NotNull(message="type은 필수입니다.")
        TimeBlockType type
) {}