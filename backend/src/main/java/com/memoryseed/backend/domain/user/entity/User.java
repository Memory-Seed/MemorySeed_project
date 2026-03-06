package com.memoryseed.backend.domain.user.entity;

import com.memoryseed.backend.global.entity.BaseTimeEntity;
import jakarta.persistence.*;

@Entity
@Table(
        name = "users",
        uniqueConstraints = {
                @UniqueConstraint(name = "uk_provider_provider_id", columnNames = {"provider", "providerId"})
        }
)
public class User extends BaseTimeEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    // KAKAO / NAVER / GOOGLE
    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 20)
    private Provider provider;

    // 각 provider에서 주는 고유 id
    @Column(nullable = false, length = 128)
    private String providerId;

    @Column(length = 100)
    private String email;

    @Column(length = 50)
    private String name;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 20)
    private UserRole role = UserRole.USER;

    protected User() {
    }

    public User(Provider provider, String providerId, String email, String name) {
        this.provider = provider;
        this.providerId = providerId;
        this.email = email;
        this.name = name;
        this.role = UserRole.USER;
    }

    // --- getters ---
    public Long getId() { return id; }
    public Provider getProvider() { return provider; }
    public String getProviderId() { return providerId; }
    public String getEmail() { return email; }
    public String getName() { return name; }
    public UserRole getRole() { return role; }

    // --- setters (필요한 것만 열어둠) ---
    public void updateProfile(String email, String name) {
        this.email = email;
        this.name = name;
    }

    public void changeRole(UserRole role) {
        this.role = role;
    }
}
