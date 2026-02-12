package com.memoryseed.backend.global.security;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpMethod;
import org.springframework.security.config.Customizer;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configurers.AbstractHttpConfigurer;
import org.springframework.security.web.SecurityFilterChain;

@Configuration
public class SecurityConfig {

    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        http
                // REST API 테스트 단계에서는 CSRF 끄는 게 편함 (Postman POST 막는 원인이 되기도 함)
                .csrf(AbstractHttpConfigurer::disable)

                // 인증/인가 규칙
                .authorizeHttpRequests(auth -> auth
                        // ✅ 배치 업로드는 임시로 열어둠
                        .requestMatchers(HttpMethod.POST, "/api/lifelog/batch").permitAll()

                        // (선택) swagger/actuator 쓸 거면 여기 추가
                        // .requestMatchers("/swagger-ui/**", "/v3/api-docs/**").permitAll()

                        // 나머지는 일단 전부 허용(테스트 단계)
                        .anyRequest().permitAll()
                )

                // 기본 로그인폼 같은 거 안 쓰고, 기본값으로 두겠다는 의미 (선택)
                .httpBasic(Customizer.withDefaults());

        return http.build();
    }
}

