package com.memoryseed.backend.global.response;

import java.time.LocalDateTime;
import java.util.List;

public record ApiErrorResponse(
        LocalDateTime timestamp,
        int status,
        String code,
        String message,
        String path,
        List<FieldErrorItem> errors
) {
    public record FieldErrorItem(
            String field,
            Object rejectedValue,
            String reason
    ) {}
}
