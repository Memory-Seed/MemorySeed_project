package com.memoryseed.backend.global.response;

import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Getter
@NoArgsConstructor
@AllArgsConstructor
public class Response<T> {
    private T data;

    public static <T> Response<T> success(T data) {
        return new Response<>(data);
    }

    public static <T> Response<T> success() {
        return new Response<>(null);
    }
}
