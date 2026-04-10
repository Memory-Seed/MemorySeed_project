package com.memoryseed.backend.domain.lifelog.service;

import com.memoryseed.backend.domain.lifelog.entity.UserCalendar;
import com.memoryseed.backend.domain.lifelog.repository.UserCalendarRepository;
import com.memoryseed.backend.domain.lifelog.dto.GoogleCalendarRequest;
import com.memoryseed.backend.domain.user.entity.User;
import com.memoryseed.backend.domain.user.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.time.OffsetDateTime;
import java.util.List;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class UserCalendarService {

    private final UserCalendarRepository userCalendarRepository;
    private final UserRepository userRepository; // 유저 확인용

    @Transactional
    public void syncGoogleCalendar(String providerId, GoogleCalendarRequest request) {
        User user = userRepository.findByProviderId(providerId)
                .orElseThrow(() -> new IllegalArgumentException("User not found with providerId: " + providerId));

        List<UserCalendar> calendars = request.getItems().stream()
                .map(item -> UserCalendar.builder()
                        .user(user)
                        .googleEventId(item.getId())
                        .summary(item.getSummary())
                        .startTime(parseDateTime(item.getStart().getDateTime()))
                        .endTime(parseDateTime(item.getEnd().getDateTime()))
                        .status(item.getStatus())
                        .build())
                .collect(Collectors.toList());

        userCalendarRepository.saveAll(calendars);
    }

    // "2025-11-26T09:00:00+09:00" 형태를 LocalDateTime으로 변환
    private LocalDateTime parseDateTime(String dateTimeStr) {
        if (dateTimeStr == null) return null;
        return OffsetDateTime.parse(dateTimeStr).toLocalDateTime();
    }
}