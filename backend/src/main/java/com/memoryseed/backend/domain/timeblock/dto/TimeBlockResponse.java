package com.memoryseed.backend.domain.timeblock.dto;

import com.memoryseed.backend.domain.timeblock.entity.TimeBlock;
import com.memoryseed.backend.domain.timeblock.entity.TimeBlockType;

import java.time.LocalDateTime;

public record TimeBlockResponse(
        Long id,
        LocalDateTime startTime,
        LocalDateTime endTime,
        TimeBlockType type,
        Integer durationMin
) {
    public static TimeBlockResponse from(TimeBlock tb) {
        return new TimeBlockResponse(
                tb.getId(),
                tb.getStartTime(),
                tb.getEndTime(),
                tb.getType(),
                tb.getDurationMin()
        );
    }
}