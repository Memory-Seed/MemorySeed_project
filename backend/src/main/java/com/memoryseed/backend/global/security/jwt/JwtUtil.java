package com.memoryseed.backend.global.security.jwt;

import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.SignatureAlgorithm;
import io.jsonwebtoken.security.Keys;
import jakarta.annotation.PostConstruct;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.nio.charset.StandardCharsets;
import java.security.Key;
import java.util.Date;

@Component
public class JwtUtil {

    // application.yml에 적어둔 비밀키를 가져옵니다.
    @Value("${jwt.secret}")
    private String secretKey;

    // application.yml에 적어둔 만료시간(밀리초)을 가져옵니다.
    @Value("${jwt.expiration}")
    private long expirationTime;

    private Key key;

    @PostConstruct
    public void init() {
        // 서버가 켜질 때, 비밀키 문자열을 가지고 진짜 '암호화 도장(Key)'을 만듭니다.
        byte[] keyBytes = secretKey.getBytes(StandardCharsets.UTF_8);
        this.key = Keys.hmacShaKeyFor(keyBytes);
    }

    /**
     * 토큰 발급 메서드 (출입증 생성기)
     * 소셜 로그인이 성공하면 이 메서드를 불러서 유저의 이메일과 권한을 담은 토큰을 만듭니다.
     */
    public String generateToken(String email, String role) {
        Date now = new Date();
        Date expiryDate = new Date(now.getTime() + expirationTime); // 현재 시간 + 24시간

        return Jwts.builder()
                .setSubject(email)             // 출입증 주인 (이메일)
                .claim("role", role)           // 추가 정보 (유저 권한)
                .setIssuedAt(now)              // 발급된 시간
                .setExpiration(expiryDate)     // 언제까지 유효한지 (만료 시간)
                .signWith(key, SignatureAlgorithm.HS256) // 우리 서버의 '비밀 도장'을 쾅! 찍음
                .compact();                    // 이 모든 걸 압축해서 하나의 문자열로 반환
    }

    /**
     * 👮 토큰 유효성 검사 (가짜 토큰이거나, 만료되었는지 확인)
     */
    public boolean validateToken(String token) {
        try {
            Jwts.parserBuilder().setSigningKey(key).build().parseClaimsJws(token);
            return true; // 에러 없이 통과하면 진짜 토큰!
        } catch (Exception e) {
            return false; // 뭐라도 에러가 나면 짭(가짜/만료) 토큰!
        }
    }

    /**
     * 🪪 토큰에서 유저 ID(providerId 또는 email) 꺼내기
     */
    public String getProviderId(String token) {
        return Jwts.parserBuilder().setSigningKey(key).build()
                .parseClaimsJws(token).getBody().getSubject();
    }

    /**
     * 🪪 토큰에서 유저 권한(Role) 꺼내기
     */
    public String getRole(String token) {
        return Jwts.parserBuilder().setSigningKey(key).build()
                .parseClaimsJws(token).getBody().get("role", String.class);
    }
}