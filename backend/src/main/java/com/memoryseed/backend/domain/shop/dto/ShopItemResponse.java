package com.memoryseed.backend.domain.shop.dto;

import com.memoryseed.backend.domain.shop.entity.ItemCategory;
import com.memoryseed.backend.domain.shop.entity.ShopItem;

public record ShopItemResponse(
        Long id,
        String code,
        String name,
        ItemCategory category,
        Integer priceCoin,
        String assetKey,
        boolean isBought
) {
    public static ShopItemResponse from(ShopItem item, boolean isBought) {
        return new ShopItemResponse(
                item.getId(),
                item.getCode(),
                item.getName(),
                item.getCategory(),
                item.getPriceCoin(),
                item.getAssetKey(),
                isBought
        );
    }
}