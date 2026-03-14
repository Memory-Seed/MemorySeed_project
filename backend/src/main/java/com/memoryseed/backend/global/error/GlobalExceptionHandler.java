package com.memoryseed.backend.global.error;

import com.memoryseed.backend.global.response.ApiErrorResponse;
import jakarta.servlet.http.HttpServletRequest;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.FieldError;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

import java.time.LocalDateTime;
import java.util.List;

@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ApiErrorResponse> handleValidation(MethodArgumentNotValidException e,
                                                             HttpServletRequest request) {

        List<ApiErrorResponse.FieldErrorItem> errors = e.getBindingResult()
                .getFieldErrors()
                .stream()
                .map(this::toItem)
                .toList();

        ApiErrorResponse body = new ApiErrorResponse(
                LocalDateTime.now(),
                HttpStatus.BAD_REQUEST.value(),
                "VALIDATION_ERROR",
                "요청 값이 올바르지 않습니다.",
                request.getRequestURI(),
                errors
        );

        return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(body);
    }

    private ApiErrorResponse.FieldErrorItem toItem(FieldError fe) {
        return new ApiErrorResponse.FieldErrorItem(
                fe.getField(),
                fe.getRejectedValue(),
                fe.getDefaultMessage()
        );
    }

    // DB 중복 제약 조건 위반 (예: 하루에 같은 퀘스트 중복 할당)
    @ExceptionHandler(org.springframework.dao.DataIntegrityViolationException.class)
    public ResponseEntity<ErrorResponse> handleDataIntegrityViolationException(org.springframework.dao.DataIntegrityViolationException e) {
        ErrorResponse response = ErrorResponse.of(
                HttpStatus.CONFLICT.value(),
                "DUPLICATE_QUEST",
                "이미 오늘 할당된 퀘스트이거나 중복된 데이터입니다."
        );
        return ResponseEntity.status(HttpStatus.CONFLICT).body(response);
    }
}
