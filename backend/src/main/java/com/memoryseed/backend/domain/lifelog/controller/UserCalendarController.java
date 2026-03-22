package com.memoryseed.backend.domain.lifelog.controller;

import com.memoryseed.backend.domain.lifelog.dto.GoogleCalendarRequest;
import com.memoryseed.backend.domain.lifelog.service.UserCalendarService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/lifelog/calendar")
@RequiredArgsConstructor
public class UserCalendarController {

    private final UserCalendarService userCalendarService;

    @PostMapping("/{userId}")
    public ResponseEntity<String> saveGoogleCalendar(
            @PathVariable Long userId,
            @RequestBody GoogleCalendarRequest request) {

        userCalendarService.syncGoogleCalendar(userId, request);
        return ResponseEntity.ok("✅ 구글 캘린더 데이터가 성공적으로 저장되었습니다.");
    }
}