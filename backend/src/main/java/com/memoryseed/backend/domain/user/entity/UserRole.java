package com.memoryseed.backend.domain.user.entity;

public enum UserRole {
    USER("ROLE_USER"),
    ADMIN("ROLE_ADMIN");

    private final String key;

    UserRole(String key) {
        this.key = key;
    }

    public String getKey() {
        return key;
    }
}
