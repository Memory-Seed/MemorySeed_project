package com.memoryseed.backend.domain.shop.controller;

import com.memoryseed.backend.domain.shop.dto.PurchaseRequest;
import com.memoryseed.backend.domain.shop.dto.PurchaseResponse;
import com.memoryseed.backend.domain.shop.dto.ShopItemResponse;
import com.memoryseed.backend.domain.shop.service.ShopService;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/shop")
public class ShopController {

    private final ShopService shopService;

    public ShopController(ShopService shopService) {
        this.shopService = shopService;
    }

    // 상점 아이템 목록
    @GetMapping("/items")
    public ResponseEntity<List<ShopItemResponse>> items() {
        return ResponseEntity.ok(shopService.listActiveItems());
    }

    // 구매 (중복구매 불가 + 코인 차감 + 인벤토리 추가)
    @PostMapping("/purchase")
    public ResponseEntity<PurchaseResponse> purchase(
            @RequestHeader("X-USER-ID") Long userId,
            @Valid @RequestBody PurchaseRequest req
    ) {
        return ResponseEntity.ok(shopService.purchase(userId, req));
    }
}