package com.memoryseed.backend.domain.pet.dto;

public record PetResponse(
        String petName,
        CustomizationState customization
) {
    public record CustomizationState(
            String hatItemCode,
            String topItemCode,
            String wallItemCode,
            String floorItemCode,
            String furnitureItemCode
    ) {}
}