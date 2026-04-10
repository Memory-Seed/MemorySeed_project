package com.memoryseed.backend.global.security;

import com.memoryseed.backend.domain.auth.service.CustomOAuth2UserService;
import com.memoryseed.backend.global.security.handler.OAuth2SuccessHandler;
import lombok.RequiredArgsConstructor;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpMethod;
import org.springframework.security.config.Customizer;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.configurers.AbstractHttpConfigurer;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;
import com.memoryseed.backend.global.security.jwt.JwtFilter;

@RequiredArgsConstructor
@Configuration
@EnableWebSecurity // 스프링 시큐리티를 명시적으로 활성화
public class SecurityConfig {

    private final CustomOAuth2UserService customOAuth2UserService;
    private final OAuth2SuccessHandler oAuth2SuccessHandler;
    private final JwtFilter jwtFilter;
    
    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        http
                // 1. CSRF 끄기 (기존 유지: Postman 테스트 및 REST API 편의)
                .csrf(AbstractHttpConfigurer::disable)

                // 2. 인증/인가 규칙 설정
                .authorizeHttpRequests(auth -> auth
                        // 라이프로그 배치 업로드 임시 허용
                        .requestMatchers(HttpMethod.POST, "/api/lifelog/batch").permitAll()

                        // 메인 화면, 로그인 관련, 에러 페이지 허용
                        .requestMatchers("/",
                                "/login/**",
                                "/oauth2/**",
                                "/v3/api-docs/**",     // 스웨거 데이터
                                "/swagger-ui/**",      // 스웨거 UI 화면
                                "/swagger-ui.html"     // 스웨거 UI 진입점).permitAll()
                        ).permitAll()
                        // 중요 변경: 기존엔 .anyRequest().permitAll() 이었지만,
                        // 로그인을 유도하려면 나머지는 "인증(로그인)해야 접근 가능"으로 변경
                        .anyRequest().authenticated()
                )

                .addFilterBefore(jwtFilter, UsernamePasswordAuthenticationFilter.class)

                // 3. OAuth2 소셜 로그인 설정 (신규)
                .oauth2Login(oauth2 -> oauth2
                        .userInfoEndpoint(userInfo -> userInfo
                                .userService(customOAuth2UserService) // "소셜 로그인 성공하면 이 클래스 실행해!"
                        )
                        .successHandler(oAuth2SuccessHandler)
                )

                // 4. HTTP Basic 기본값 설정 (기존 유지)
                .httpBasic(Customizer.withDefaults());

        return http.build();
    }
}