package com.memoryseed.backend.domain.pet.entity;

import com.memoryseed.backend.domain.shop.entity.ShopItem;
import com.memoryseed.backend.domain.user.entity.User;
import com.memoryseed.backend.global.entity.BaseTimeEntity;
import jakarta.persistence.*;
import lombok.AccessLevel;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Entity
@Table(name = "pet_customizations")
@Getter
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class PetCustomization extends BaseTimeEntity {

    @Id
    @Column(name = "user_id")
    private Long userId;

    @MapsId
    @OneToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "user_id")
    private User user;

    // outfit
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "hat_item_id")
    private ShopItem hatItem;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "top_item_id")
    private ShopItem topItem;

    // room
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "wall_item_id")
    private ShopItem wallItem;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "floor_item_id")
    private ShopItem floorItem;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "furniture_item_id")
    private ShopItem furnitureItem;

    public PetCustomization(User user) {
        this.user = user;
    }

    public void apply(ShopItem hat, ShopItem top, ShopItem wall, ShopItem floor, ShopItem furniture) {
        this.hatItem = hat;
        this.topItem = top;
        this.wallItem = wall;
        this.floorItem = floor;
        this.furnitureItem = furniture;
    }
}