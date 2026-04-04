package com.memoryseed.backend.global.security;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpMethod;
import org.springframework.security.config.Customizer;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.configurers.AbstractHttpConfigurer;
import org.springframework.security.web.SecurityFilterChain;

@Configuration
@EnableWebSecurity // 스프링 시큐리티를 명시적으로 활성화
public class SecurityConfig {

    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        http
                // 1. CSRF 끄기 (기존 유지: Postman 테스트 및 REST API 편의)
                .csrf(AbstractHttpConfigurer::disable)

                // 2. 인증/인가 규칙 설정
                .authorizeHttpRequests(auth -> auth
                        // ✅ 기존: 라이프로그 배치 업로드 임시 허용
                        .requestMatchers(HttpMethod.POST, "/api/lifelog/batch").permitAll()

                        // ✅ 신규: 메인 화면, 로그인 관련, 에러 페이지 허용
                        .requestMatchers("/", "/login**", "/error").permitAll()

                        // 🚨 중요 변경: 기존엔 .anyRequest().permitAll() 이었지만,
                        // 로그인을 유도하려면 나머지는 "인증(로그인)해야 접근 가능"으로 바꿔야 합니다!
                        .anyRequest().authenticated()
                )

                // 3. OAuth2 소셜 로그인 설정 (신규)
                .oauth2Login(oauth2 -> oauth2
                        .defaultSuccessUrl("/") // 로그인 성공 시 메인 화면으로 이동
                )

                // 4. HTTP Basic 기본값 설정 (기존 유지)
                .httpBasic(Customizer.withDefaults());

        return http.build();
    }
}