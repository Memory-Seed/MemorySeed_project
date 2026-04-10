package com.memoryseed.backend.domain.lifelog.dto;

import lombok.Getter;
import lombok.NoArgsConstructor;
import java.util.List;

@Getter
@NoArgsConstructor
public class GoogleCalendarRequest {
    private List<EventItem> items;

    @Getter
    @NoArgsConstructor
    public static class EventItem {
        private String id;
        private String summary;
        private TimeInfo start;
        private TimeInfo end;
        private String status;
    }

    @Getter
    @NoArgsConstructor
    public static class TimeInfo {
        private String dateTime; // "2025-11-26T09:00:00+09:00" 형태
    }
}