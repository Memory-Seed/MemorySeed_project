package com.memoryseed.backend.domain.shop.dto;

public record PurchaseResponse(
        String itemCode,
        Integer remainingCoins
) {}