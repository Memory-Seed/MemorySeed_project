package com.memoryseed.backend.domain.user.repository;

import com.memoryseed.backend.domain.user.entity.Provider;
import com.memoryseed.backend.domain.user.entity.User;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;

public interface UserRepository extends JpaRepository<User, Long> {

    Optional<User> findByProviderAndProviderId(Provider provider, String providerId);

    boolean existsByProviderAndProviderId(Provider provider, String providerId);
}
