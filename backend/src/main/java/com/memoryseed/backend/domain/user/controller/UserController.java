package com.memoryseed.backend.domain.user.controller;

import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/users")
public class UserController {

    // 토큰이 있는 사람만 들어올 수 있는 API
    @GetMapping("/me")
    public String getMyInfo(Authentication authentication) {
        // JwtFilter(문지기)가 통과시켜준 유저의 ID를 꺼냅니다.
        String providerId = authentication.getName();

        return "당신의 고유 ID는 [" + providerId + "] 입니다.";
    }
}