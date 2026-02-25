// C:/Users/rlaeh/Desktop/인천대학교/캡스톤 디자인/MemorySeed_project/backend/src/main/java/com/memoryseed/backend/domain/lifelog/external/weather/AccuWeatherClient.java
package com.memoryseed.backend.domain.lifelog.external.weather;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Component;
import org.springframework.web.client.HttpClientErrorException;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.server.ResponseStatusException;
import org.springframework.web.util.UriComponentsBuilder;

@Slf4j
@Component
@RequiredArgsConstructor
public class AccuWeatherClient {

    private final RestTemplate restTemplate;
    private final ObjectMapper objectMapper; // ObjectMapper는 spring-boot-starter-web에 의해 자동 구성됩니다.

    @Value("${accuweather.api-key}")
    private String apiKey;

    @Value("${accuweather.base-url}") // application.properties에서 base-url 주입
    private String baseUrl;

    // 1. 위경도로 Location Key 가져오기
    public String getLocationKey(Double lat, Double lon) {
        String url = UriComponentsBuilder.fromHttpUrl(baseUrl + "/locations/v1/cities/geoposition/search")
                .queryParam("apikey", apiKey)
                .queryParam("q", lat + "," + lon)
                .toUriString();

        try {
            String response = restTemplate.getForObject(url, String.class);
            JsonNode root = objectMapper.readTree(response);
            if (root != null && root.has("Key")) {
                return root.get("Key").asText();
            }
            throw new ResponseStatusException(HttpStatus.NOT_FOUND, "AccuWeather Location Key를 찾을 수 없습니다.");
        } catch (HttpClientErrorException e) {
            log.error("AccuWeather Location Key 조회 실패 (HTTP {}): {}", e.getStatusCode(), e.getResponseBodyAsString());
            throw new ResponseStatusException(e.getStatusCode(), "AccuWeather Location Key 조회 실패: " + e.getMessage());
        } catch (Exception e) {
            log.error("AccuWeather Location Key 조회 중 예상치 못한 오류 발생: {}", e.getMessage(), e);
            throw new ResponseStatusException(HttpStatus.INTERNAL_SERVER_ERROR, "AccuWeather Location Key 조회 중 오류 발생");
        }
    }

    // 2. 현재 날씨 조회
    public JsonNode getCurrentConditions(String locationKey) {
        String url = UriComponentsBuilder.fromHttpUrl(baseUrl + "/currentconditions/v1/" + locationKey)
                .queryParam("apikey", apiKey)
                .queryParam("details", "true") // 습도 등 상세 정보
                .toUriString();

        try {
            String response = restTemplate.getForObject(url, String.class);
            JsonNode root = objectMapper.readTree(response);
            // 배열 형태로 오므로 첫 번째 요소 반환
            if (root.isArray() && root.size() > 0) {
                return root.get(0);
            }
            throw new ResponseStatusException(HttpStatus.NOT_FOUND, "AccuWeather 현재 날씨 정보를 찾을 수 없습니다.");
        } catch (HttpClientErrorException e) {
            log.error("AccuWeather 날씨 조회 실패 (HTTP {}): {}", e.getStatusCode(), e.getResponseBodyAsString());
            throw new ResponseStatusException(e.getStatusCode(), "AccuWeather 날씨 조회 실패: " + e.getMessage());
        } catch (Exception e) {
            log.error("AccuWeather 날씨 조회 중 예상치 못한 오류 발생: {}", e.getMessage(), e);
            throw new ResponseStatusException(HttpStatus.INTERNAL_SERVER_ERROR, "AccuWeather 날씨 조회 중 오류 발생");
        }
    }
}