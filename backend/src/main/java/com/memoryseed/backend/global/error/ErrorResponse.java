package com.memoryseed.backend.global.error;

import lombok.Builder;
import lombok.Getter;

@Getter
@Builder
public class ErrorResponse {
    private final int status;
    private final String error;
    private final String message;

    public static ErrorResponse of(int status, String error, String message) {
        return ErrorResponse.builder()
                .status(status)
                .error(error)
                .message(message)
                .build();
    }
}