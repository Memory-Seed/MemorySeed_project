package com.memoryseed.backend.domain.lifelog.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.memoryseed.backend.domain.lifelog.dto.LocationDto;
import com.memoryseed.backend.domain.lifelog.dto.WeatherResponseDto;
import com.memoryseed.backend.domain.lifelog.entity.CollectionRun;
import com.memoryseed.backend.domain.lifelog.entity.WeatherTimeseries;
import com.memoryseed.backend.domain.lifelog.external.weather.AccuWeatherClient;
import com.memoryseed.backend.domain.lifelog.repository.WeatherTimeseriesRepository;
import com.memoryseed.backend.domain.user.entity.User;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;

@Slf4j
@Service
@RequiredArgsConstructor
public class WeatherIngestService {

    private final AccuWeatherClient accuWeatherClient;
    private final WeatherTimeseriesRepository weatherRepository;

    /**
     * run마다 들어오는 location(lat/lon)으로 AccuWeather 호출 후,
     * weather_timeseries에 1건 저장하고, 응답 DTO를 반환
     */
    @Transactional
    public WeatherResponseDto fetchAndSaveWeather(User user, CollectionRun run, LocationDto location) {
        if (user == null || run == null || location == null) return null;

        // 1) locationKey 조회
        String locationKey = accuWeatherClient.getLocationKey(location.lat(), location.lon());
        if (locationKey == null || locationKey.isBlank()) {
            log.warn("AccuWeather locationKey 조회 실패");
            return null;
        }

        // 2) current conditions 조회
        JsonNode weatherNode = accuWeatherClient.getCurrentConditions(locationKey);
        if (weatherNode == null || weatherNode.isEmpty()) {
            log.warn("AccuWeather current conditions 응답 비어있음");
            return null;
        }

        // 3) 필요한 값 파싱 (DB에는 최소만 저장)
        String condition = readText(weatherNode, "WeatherText"); // ex) "Cloudy"
        Double temperatureC = readTemperatureC(weatherNode);     // Temperature.Metric.Value
        Integer pm10 = null; // 지금 단계에서는 AirQuality API 따로라서 null

        LocalDateTime measuredAt = run.getRunAt(); // runAt을 time으로 저장 (원하면 now()로 바꿔도 됨)

        // 4) 엔티티 생성/저장 (setter 쓰지 말고 생성자 사용)
        WeatherTimeseries weather = new WeatherTimeseries(
                user,
                run,
                measuredAt,
                temperatureC,
                pm10,
                condition
        );

        weatherRepository.save(weather);

        // 5) 화면 표시용 DTO(조언 포함)
        return createResponse(temperatureC, condition, readInt(weatherNode, "WeatherIcon"));
    }

    private Double readTemperatureC(JsonNode node) {
        try {
            JsonNode temp = node.get("Temperature");
            if (temp == null) return null;
            JsonNode metric = temp.get("Metric");
            if (metric == null) return null;
            JsonNode value = metric.get("Value");
            if (value == null || value.isNull()) return null;
            return value.asDouble();
        } catch (Exception e) {
            return null;
        }
    }

    private String readText(JsonNode node, String field) {
        JsonNode v = node.get(field);
        return (v == null || v.isNull()) ? null : v.asText();
    }

    private Integer readInt(JsonNode node, String field) {
        JsonNode v = node.get(field);
        return (v == null || v.isNull()) ? null : v.asInt();
    }

    private WeatherResponseDto createResponse(Double tempC, String condition, Integer icon) {
        String advice = "좋은 하루 보내세요!";
        String text = condition == null ? "" : condition.toLowerCase();

        if (text.contains("rain") || text.contains("shower")) {
            advice = "비가 올 수 있어요. 우산을 챙기세요! ☔";
        } else if (text.contains("snow")) {
            advice = "눈길 조심하세요! 따뜻하게 입으세요. 🧣";
        } else if (tempC != null && tempC > 30) {
            advice = "매우 더운 날씨입니다. 수분 섭취 잊지 마세요! 💧";
        } else if (tempC != null && tempC < 5) {
            advice = "날씨가 춥습니다. 목도리를 추천해요. 🧤";
        } else if (text.contains("sunny") || text.contains("clear")) {
            advice = "화창한 날씨네요! 가벼운 산책 어때요? ☀️";
        }

        return WeatherResponseDto.builder()
                .temperature(tempC)
                .weatherText(condition)
                .weatherIcon(icon)
                .adviceMessage(advice)
                .build();
    }
}