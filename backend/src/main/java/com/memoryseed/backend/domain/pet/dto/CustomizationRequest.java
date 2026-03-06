package com.memoryseed.backend.domain.pet.dto;

public record CustomizationRequest(
        String hatItemCode,
        String topItemCode,
        String wallItemCode,
        String floorItemCode,
        String furnitureItemCode
) {}