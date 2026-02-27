package com.memoryseed.backend.domain.shop.repository;

import com.memoryseed.backend.domain.shop.entity.ShopItem;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;

public interface ShopItemRepository extends JpaRepository<ShopItem, Long> {
    Optional<ShopItem> findByCode(String code);
}