package com.memoryseed.backend.domain.shop.service;

import com.memoryseed.backend.domain.shop.dto.PurchaseRequest;
import com.memoryseed.backend.domain.shop.dto.PurchaseResponse;
import com.memoryseed.backend.domain.shop.dto.ShopItemResponse;
import com.memoryseed.backend.domain.shop.entity.ShopItem;
import com.memoryseed.backend.domain.shop.entity.UserInventory;
import com.memoryseed.backend.domain.shop.repository.ShopItemRepository;
import com.memoryseed.backend.domain.shop.repository.UserInventoryRepository;
import com.memoryseed.backend.domain.user.entity.User;
import com.memoryseed.backend.domain.user.repository.UserRepository;
import com.memoryseed.backend.domain.wallet.entity.UserWallet;
import com.memoryseed.backend.domain.wallet.repository.UserWalletRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.time.ZoneId;
import java.util.List;
import java.util.Set;
import java.util.stream.Collectors;

@Service
public class ShopService {

    private final ShopItemRepository shopItemRepository;
    private final UserInventoryRepository userInventoryRepository;
    private final UserRepository userRepository;
    private final UserWalletRepository userWalletRepository;

    public ShopService(
            ShopItemRepository shopItemRepository,
            UserInventoryRepository userInventoryRepository,
            UserRepository userRepository,
            UserWalletRepository userWalletRepository
    ) {
        this.shopItemRepository = shopItemRepository;
        this.userInventoryRepository = userInventoryRepository;
        this.userRepository = userRepository;
        this.userWalletRepository = userWalletRepository;
    }

    @Transactional(readOnly = true)
    public List<ShopItemResponse> listActiveItems() {
        // This method will now use the new from() method with isBought = false by default
        return shopItemRepository.findAll().stream()
                .filter(ShopItem::getActive)
                .map(item -> ShopItemResponse.from(item, false)) // Default to false for general listing
                .toList();
    }

    @Transactional(readOnly = true)
    public List<ShopItemResponse> listShopItemsWithPurchaseStatus(String providerId) {
        User user = userRepository.findByProviderId(providerId)
                .orElseThrow(() -> new IllegalArgumentException("User not found with providerId: " + providerId));

        List<ShopItem> activeShopItems = shopItemRepository.findAll().stream()
                .filter(ShopItem::getActive)
                .toList();

        Set<Long> purchasedItemIds = userInventoryRepository.findAllByUser(user).stream()
                .map(userInventory -> userInventory.getItem().getId())
                .collect(Collectors.toSet());

        return activeShopItems.stream()
                .map(item -> ShopItemResponse.from(item, purchasedItemIds.contains(item.getId())))
                .toList();
    }

    @Transactional
    public PurchaseResponse purchase(String providerId, PurchaseRequest req) {
        User user = userRepository.findByProviderId(providerId)
                .orElseThrow(() -> new IllegalArgumentException("User not found with providerId: " + providerId));

        ShopItem item = shopItemRepository.findByCode(req.itemCode())
                .orElseThrow(() -> new IllegalArgumentException("item not found: " + req.itemCode()));

        if (!Boolean.TRUE.equals(item.getActive())) {
            throw new IllegalStateException("item is not active: " + item.getCode());
        }

        // 중복 구매 불가
        if (userInventoryRepository.existsByUserAndItem(user, item)) {
            throw new IllegalStateException("already purchased item: " + item.getCode());
        }

        // 지갑 없으면 생성(초기 개발 편의)
        UserWallet wallet = userWalletRepository.findById(user.getId())
                .orElseGet(() -> userWalletRepository.save(new UserWallet(user)));

        // 코인 차감
        wallet.subtractCoins(item.getPriceCoin());

        // 인벤토리 저장
        LocalDateTime now = LocalDateTime.now(ZoneId.of("Asia/Seoul"));
        userInventoryRepository.save(new UserInventory(user, item, now));

        // wallet은 영속 상태라 flush 시점에 반영됨
        return new PurchaseResponse(item.getCode(), wallet.getCoinBalance());
    }
}