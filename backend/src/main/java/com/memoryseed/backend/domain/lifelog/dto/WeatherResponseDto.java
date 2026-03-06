package com.memoryseed.backend.domain.lifelog.dto;

import lombok.Builder;
import lombok.Data;

@Data
@Builder
public class WeatherResponseDto {
    private Double temperature;
    private String weatherText;     // "Sunny", "Rain" 등
    private Integer weatherIcon;    // AccuWeather 아이콘 ID
    private String adviceMessage;   // "우산을 챙기세요!"
}