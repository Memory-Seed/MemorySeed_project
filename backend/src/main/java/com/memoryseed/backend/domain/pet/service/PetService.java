package com.memoryseed.backend.domain.pet.service;

import com.memoryseed.backend.domain.pet.dto.CustomizationRequest;
import com.memoryseed.backend.domain.pet.dto.PetResponse;
import com.memoryseed.backend.domain.pet.entity.Pet;
import com.memoryseed.backend.domain.pet.entity.PetCustomization;
import com.memoryseed.backend.domain.pet.repository.PetCustomizationRepository;
import com.memoryseed.backend.domain.pet.repository.PetRepository;
import com.memoryseed.backend.domain.shop.entity.ItemCategory;
import com.memoryseed.backend.domain.shop.entity.ShopItem;
import com.memoryseed.backend.domain.shop.repository.ShopItemRepository;
import com.memoryseed.backend.domain.shop.repository.UserInventoryRepository;
import com.memoryseed.backend.domain.user.entity.User;
import com.memoryseed.backend.domain.user.repository.UserRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class PetService {

    private final UserRepository userRepository;
    private final PetRepository petRepository;
    private final PetCustomizationRepository customizationRepository;
    private final ShopItemRepository shopItemRepository;
    private final UserInventoryRepository inventoryRepository;

    public PetService(
            UserRepository userRepository,
            PetRepository petRepository,
            PetCustomizationRepository customizationRepository,
            ShopItemRepository shopItemRepository,
            UserInventoryRepository inventoryRepository
    ) {
        this.userRepository = userRepository;
        this.petRepository = petRepository;
        this.customizationRepository = customizationRepository;
        this.shopItemRepository = shopItemRepository;
        this.inventoryRepository = inventoryRepository;
    }

    @Transactional(readOnly = true)
    public PetResponse getPet(String providerId) {
        User user = userRepository.findByProviderId(providerId)
                .orElseThrow(() -> new IllegalArgumentException("User not found with providerId: " + providerId));

        Pet pet = petRepository.findByUser(user)
                .orElseThrow(() -> new IllegalStateException("pet not found for user: " + user.getId()));

        PetCustomization c = customizationRepository.findById(user.getId())
                .orElse(null);

        return new PetResponse(
                pet.getName(),
                new PetResponse.CustomizationState(
                        codeOf(c == null ? null : c.getHatItem()),
                        codeOf(c == null ? null : c.getTopItem()),
                        codeOf(c == null ? null : c.getWallItem()),
                        codeOf(c == null ? null : c.getFloorItem()),
                        codeOf(c == null ? null : c.getFurnitureItem())
                )
        );
    }

    @Transactional
    public PetResponse applyCustomization(String providerId, CustomizationRequest req) {
        User user = userRepository.findByProviderId(providerId)
                .orElseThrow(() -> new IllegalArgumentException("User not found with providerId: " + providerId));

        Pet pet = petRepository.findByUser(user)
                .orElseThrow(() -> new IllegalStateException("pet not found for user: " + user.getId()));

        PetCustomization c = customizationRepository.findById(user.getId())
                .orElseGet(() -> customizationRepository.save(new PetCustomization(user)));

        // 기존 값 가져오기
        ShopItem hat = c.getHatItem();
        ShopItem top = c.getTopItem();
        ShopItem wall = c.getWallItem();
        ShopItem floor = c.getFloorItem();
        ShopItem furniture = c.getFurnitureItem();

        // 요청이 들어온 슬롯만 교체
        if (req.hatItemCode() != null) {
            hat = requireOwnedItem(user, req.hatItemCode(), ItemCategory.HAT);
        }
        if (req.topItemCode() != null) {
            top = requireOwnedItem(user, req.topItemCode(), ItemCategory.TOP);
        }
        if (req.wallItemCode() != null) {
            wall = requireOwnedItem(user, req.wallItemCode(), ItemCategory.WALL);
        }
        if (req.floorItemCode() != null) {
            floor = requireOwnedItem(user, req.floorItemCode(), ItemCategory.FLOOR);
        }
        if (req.furnitureItemCode() != null) {
            furniture = requireOwnedItem(user, req.furnitureItemCode(), ItemCategory.FURNITURE);
        }

        c.apply(hat, top, wall, floor, furniture);

        return new PetResponse(
                pet.getName(),
                new PetResponse.CustomizationState(
                        codeOf(hat),
                        codeOf(top),
                        codeOf(wall),
                        codeOf(floor),
                        codeOf(furniture)
                )
        );
    }

    private ShopItem requireOwnedItem(User user, String itemCode, ItemCategory expectedCategory) {
        ShopItem item = shopItemRepository.findByCode(itemCode)
                .orElseThrow(() -> new IllegalArgumentException("item not found: " + itemCode));

        if (!Boolean.TRUE.equals(item.getActive())) {
            throw new IllegalStateException("item is not active: " + itemCode);
        }

        if (item.getCategory() != expectedCategory) {
            throw new IllegalArgumentException("category mismatch. expected=" + expectedCategory + ", actual=" + item.getCategory());
        }

        if (!inventoryRepository.existsByUserAndItem(user, item)) {
            throw new IllegalStateException("user does not own item: " + itemCode);
        }

        return item;
    }

    private String codeOf(ShopItem item) {
        return item == null ? null : item.getCode();
    }
}