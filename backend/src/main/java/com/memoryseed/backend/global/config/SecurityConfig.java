package com.memoryseed.backend.global.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.web.SecurityFilterChain;

@Configuration
@EnableWebSecurity // 스프링 시큐리티를 활성화합니다.
public class SecurityConfig {

    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        http
                // 1. CSRF 공격 방어 기능 끄기 (캡스톤/로컬 테스트의 편의를 위해 일단 끕니다)
                .csrf(csrf -> csrf.disable())

                // 2. 접근 권한 설정
                .authorizeHttpRequests(auth -> auth
                        .requestMatchers("/", "/login**", "/error").permitAll() // 메인 화면, 로그인 페이지, 에러 페이지는 누구나 접근 가능
                        .anyRequest().authenticated() // 그 외의 모든 요청은 "로그인한 유저만" 접근 가능
                )

                // 3. OAuth2 소셜 로그인 설정
                .oauth2Login(oauth2 -> oauth2
                        .defaultSuccessUrl("/") // 로그인 성공하면 메인 화면("/")으로 이동시켜라
                );

        return http.build();
    }
}