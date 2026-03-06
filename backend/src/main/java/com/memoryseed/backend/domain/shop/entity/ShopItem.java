package com.memoryseed.backend.domain.shop.entity;

import com.memoryseed.backend.global.entity.BaseTimeEntity;
import jakarta.persistence.*;
import lombok.AccessLevel;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Entity
@Table(
        name = "shop_items",
        uniqueConstraints = @UniqueConstraint(name = "uk_shop_item_code", columnNames = "code"),
        indexes = @Index(name = "idx_shop_item_category", columnList = "category")
)
@Getter
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class ShopItem extends BaseTimeEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(length = 50, nullable = false, unique = true)
    private String code;

    @Column(length = 100, nullable = false)
    private String name;

    @Enumerated(EnumType.STRING)
    @Column(length = 30, nullable = false)
    private ItemCategory category;

    @Column(nullable = false)
    private Integer priceCoin;

    @Column(length = 100, nullable = false)
    private String assetKey;

    @Column(nullable = false)
    private Boolean active = true;

    public ShopItem(String code, String name, ItemCategory category, int priceCoin, String assetKey) {
        this.code = code;
        this.name = name;
        this.category = category;
        this.priceCoin = priceCoin;
        this.assetKey = assetKey;
        this.active = true;
    }

    public void deactivate() {
        this.active = false;
    }
}