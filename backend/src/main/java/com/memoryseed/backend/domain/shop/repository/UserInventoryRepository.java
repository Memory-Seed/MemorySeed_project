package com.memoryseed.backend.domain.shop.repository;

import com.memoryseed.backend.domain.shop.entity.ShopItem;
import com.memoryseed.backend.domain.shop.entity.UserInventory;
import com.memoryseed.backend.domain.user.entity.User;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;

public interface UserInventoryRepository extends JpaRepository<UserInventory, Long> {
    boolean existsByUserAndItem(User user, ShopItem item);
    List<UserInventory> findAllByUser(User user);
    Optional<UserInventory> findByUserAndItem(User user, ShopItem item);
}