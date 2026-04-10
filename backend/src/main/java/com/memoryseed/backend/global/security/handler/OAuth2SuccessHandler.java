package com.memoryseed.backend.global.security.handler;

import com.memoryseed.backend.global.security.jwt.JwtUtil;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.security.core.Authentication;
import org.springframework.security.oauth2.core.user.OAuth2User;
import org.springframework.security.web.authentication.SimpleUrlAuthenticationSuccessHandler;
import org.springframework.stereotype.Component;

import java.io.IOException;

@Component
@RequiredArgsConstructor
public class OAuth2SuccessHandler extends SimpleUrlAuthenticationSuccessHandler {

    private final JwtUtil jwtUtil;

    @Override
    public void onAuthenticationSuccess(HttpServletRequest request, HttpServletResponse response, Authentication authentication) throws IOException, ServletException {
        // 1. 방금 로그인 성공한 유저의 정보 가져오기
        OAuth2User oAuth2User = (OAuth2User) authentication.getPrincipal();

        // 2. 토큰에 넣을 식별자(ID)와 권한(Role) 뽑기
        // (getName()을 쓰면 카카오는 회원번호, 구글은 sub 등 고유 식별자가 나옵니다)
        String providerId = oAuth2User.getName();
        String role = authentication.getAuthorities().iterator().next().getAuthority();

        // 3. JwtUtil 공장을 돌려서 진짜 토큰(문자열) 뽑아내기
        String token = jwtUtil.generateToken(providerId, role);

        // 4. 프론트엔드 주소로 리다이렉트 (토큰을 쿼리스트링에 달아서 보냅니다)
        // 🚨 프론트엔드(React, Vue 등)가 실행 중인 주소에 맞게 포트 번호를 꼭 수정해 주세요! (보통 3000이나 5173을 씁니다)
        String targetUrl = "http://localhost:3000/oauth2/redirect?token=" + token;

        // 5. 유저를 프론트엔드로 강제 이동! 출발!
        getRedirectStrategy().sendRedirect(request, response, targetUrl);
    }
}