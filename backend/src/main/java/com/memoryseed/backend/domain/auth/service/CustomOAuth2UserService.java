package com.memoryseed.backend.domain.auth.service;

import com.memoryseed.backend.domain.user.entity.Provider;
import com.memoryseed.backend.domain.user.entity.User;
import com.memoryseed.backend.domain.user.entity.UserRole;
import com.memoryseed.backend.domain.user.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.oauth2.client.userinfo.DefaultOAuth2UserService;
import org.springframework.security.oauth2.client.userinfo.OAuth2UserRequest;
import org.springframework.security.oauth2.core.OAuth2AuthenticationException;
import org.springframework.security.oauth2.core.user.DefaultOAuth2User;
import org.springframework.security.oauth2.core.user.OAuth2User;
import org.springframework.stereotype.Service;

import java.util.Collections;
import java.util.Map;

@Service
@RequiredArgsConstructor
public class CustomOAuth2UserService extends DefaultOAuth2UserService {

    private final UserRepository userRepository;

    @Override
    public OAuth2User loadUser(OAuth2UserRequest userRequest) throws OAuth2AuthenticationException {
        OAuth2User oAuth2User = super.loadUser(userRequest);
        String registrationId = userRequest.getClientRegistration().getRegistrationId();

        // ✅ 수정: 복잡하게 가져오지 말고, 확실하게 구글은 "sub", 카카오는 "id"로 못 박아줍니다!
        String userNameAttributeName = "id"; // 기본값 (카카오 등)
        if ("google".equals(registrationId)) {
            userNameAttributeName = "sub"; // 구글일 때만 "sub"로 변경
        }
        String providerId = "";
        String email = "no-email@test.com"; // 기본값
        String nickname = "임시유저"; // 기본값
        Provider provider = null;

        Map<String, Object> attributes = oAuth2User.getAttributes();

        // 1. 카카오 파싱
        if ("kakao".equals(registrationId)) {
            provider = Provider.KAKAO;
            providerId = attributes.get("id").toString();

            Map<String, Object> kakaoAccount = (Map<String, Object>) attributes.get("kakao_account");
            if (kakaoAccount != null) {
                if (kakaoAccount.get("email") != null) {
                    email = (String) kakaoAccount.get("email");
                }
                Map<String, Object> profile = (Map<String, Object>) kakaoAccount.get("profile");
                if (profile != null && profile.get("nickname") != null) {
                    nickname = (String) profile.get("nickname");
                }
            }
        }
        // 🚨 수정 포인트 2: 카카오 if문 괄호 바깥으로 구글 파싱을 빼냈습니다!
        else if ("google".equals(registrationId)) {
            provider = Provider.GOOGLE;
            providerId = attributes.get("sub").toString();

            if (attributes.get("email") != null) {
                email = (String) attributes.get("email");
            }
            if (attributes.get("name") != null) {
                nickname = (String) attributes.get("name");
            }
        }

        // 2차 강력 방어막: 구글/카카오에 맞게 임시 닉네임 생성
        if (nickname == null || nickname.trim().isEmpty()) {
            nickname = registrationId + "_" + System.currentTimeMillis();
        }

        // 디버깅: 콘솔 창 확인용
        System.out.println("==== [소셜 로그인 디버깅] ====");
        System.out.println("Provider: " + provider);
        System.out.println("ProviderId: " + providerId);
        System.out.println("Email: " + email);
        System.out.println("Nickname: [" + nickname + "]");
        System.out.println("=============================");

        Provider finalProvider = provider;
        String finalProviderId = providerId;
        String finalEmail = email;
        String finalNickname = nickname;

        User user = userRepository.findByProviderAndProviderId(provider, providerId)
                .orElseGet(() -> {
                    User newUser = User.builder()
                            .provider(finalProvider)
                            .providerId(finalProviderId)
                            .email(finalEmail)
                            .nickname(finalNickname)
                            .role(UserRole.USER)
                            .build();
                    return userRepository.save(newUser);
                });

        return new DefaultOAuth2User(
                Collections.singleton(new SimpleGrantedAuthority(user.getRole().getKey())),
                attributes,
                userNameAttributeName // 🚨 수정 포인트 3: "id" 하드코딩 제거하고 동적 키값 사용
        );
    }
}