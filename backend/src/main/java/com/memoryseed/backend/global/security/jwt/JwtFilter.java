package com.memoryseed.backend.global.security.jwt;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;
import java.util.Collections;

@Component
@RequiredArgsConstructor
public class JwtFilter extends OncePerRequestFilter {

    private final JwtUtil jwtUtil;

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain filterChain)
            throws ServletException, IOException {

        // 1. 프론트엔드가 보낸 봉투(Header)에서 'Authorization' 칸을 열어봅니다.
        String authorizationHeader = request.getHeader("Authorization");

        // 2. 봉투에 토큰이 있고, 'Bearer '로 시작하는지 확인합니다.
        if (authorizationHeader != null && authorizationHeader.startsWith("Bearer ")) {
            // 'Bearer ' 글자를 떼어내고 순수 토큰 문자열만 추출합니다. (7글자)
            String token = authorizationHeader.substring(7);

            // 3. 토큰이 진짜인지(유효한지) 검사합니다.
            if (jwtUtil.validateToken(token)) {
                // 4. 진짜 토큰이라면, 안에 있는 유저 정보를 꺼냅니다.
                String providerId = jwtUtil.getProviderId(token);
                String role = jwtUtil.getRole(token);

                // 5. 스프링 시큐리티에게 "이 사람 정상적으로 신분증 확인됐어! 통과시켜 줘!" 라고 보고서(Authentication)를 제출합니다.
                UsernamePasswordAuthenticationToken authenticationToken = new UsernamePasswordAuthenticationToken(
                        providerId, null, Collections.singleton(new SimpleGrantedAuthority(role))
                );
                SecurityContextHolder.getContext().setAuthentication(authenticationToken);
            }
        }

        // 6. 검사가 끝났으니 다음 단계(또는 컨트롤러)로 넘겨줍니다.
        filterChain.doFilter(request, response);
    }
}