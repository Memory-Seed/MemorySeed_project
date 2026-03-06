package com.memoryseed.backend.global.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.client.RestClient;

@Configuration
public class AccuWeatherConfig {

    @Bean
    RestClient accuWeatherRestClient() {
        return RestClient.builder().build();
    }
}
