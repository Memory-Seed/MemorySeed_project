package com.memoryseed.backend.domain.user.repository;

import com.memoryseed.backend.domain.user.entity.Provider;
import com.memoryseed.backend.domain.user.entity.User;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;

public interface UserRepository extends JpaRepository<User, Long> {

    //  소셜 로그인용 식별 메서드
    Optional<User> findByProviderAndProviderId(Provider provider, String providerId);
    boolean existsByProviderAndProviderId(Provider provider, String providerId);
    Optional<User> findByProviderId(String providerId);

    // 이메일 중복 검사나 이메일 기반 로직이 필요할 때를 대비한 메서드
    Optional<User> findByEmail(String email);
}
