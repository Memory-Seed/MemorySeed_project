package com.memoryseed.backend.domain.shop.dto;

import jakarta.validation.constraints.NotBlank;

public record PurchaseRequest(
        @NotBlank(message = "itemCode는 필수입니다.")
        String itemCode
) {}