package com.memoryseed.backend.domain.shop.entity;

import com.memoryseed.backend.domain.user.entity.User;
import com.memoryseed.backend.global.entity.BaseTimeEntity;
import jakarta.persistence.*;
import lombok.AccessLevel;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

@Entity
@Table(
        name = "user_inventory",
        uniqueConstraints = @UniqueConstraint(name = "uk_inventory_user_item", columnNames = {"user_id", "item_id"}),
        indexes = @Index(name = "idx_inventory_user", columnList = "user_id")
)
@Getter
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class UserInventory extends BaseTimeEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "user_id", nullable = false)
    private User user;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "item_id", nullable = false)
    private ShopItem item;

    @Column(nullable = false)
    private LocalDateTime purchasedAt;

    public UserInventory(User user, ShopItem item, LocalDateTime purchasedAt) {
        this.user = user;
        this.item = item;
        this.purchasedAt = purchasedAt;
    }
}