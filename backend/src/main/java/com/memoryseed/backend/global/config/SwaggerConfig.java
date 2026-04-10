package com.memoryseed.backend.global.config;

import io.swagger.v3.oas.models.Components;
import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Info;
import io.swagger.v3.oas.models.security.SecurityRequirement;
import io.swagger.v3.oas.models.security.SecurityScheme;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class SwaggerConfig {

    @Bean
    public OpenAPI openAPI() {
        // 1. JWT 보안 체계 설정 (화면 우측 상단에 자물쇠 버튼 만들기)
        String jwtSchemeName = "JWT Auth";
        SecurityRequirement securityRequirement = new SecurityRequirement().addList(jwtSchemeName);

        Components components = new Components()
                .addSecuritySchemes(jwtSchemeName, new SecurityScheme()
                        .name(jwtSchemeName)
                        .type(SecurityScheme.Type.HTTP) // HTTP 방식
                        .scheme("bearer")               // Bearer 토큰
                        .bearerFormat("JWT"));          // 포맷은 JWT

        // 2. 스웨거 메인 설명서 정보 세팅
        Info info = new Info()
                .title("MemorySeed API 명세서")
                .description("MemorySeed 프론트엔드 연동을 위한 API 문서입니다.")
                .version("v1.0.0");

        return new OpenAPI()
                .info(info)
                .addSecurityItem(securityRequirement)
                .components(components);
    }
}