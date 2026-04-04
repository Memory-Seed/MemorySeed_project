package com.memoryseed.backend.domain.shop.controller;

import com.memoryseed.backend.domain.shop.dto.PurchaseRequest;
import com.memoryseed.backend.domain.shop.dto.PurchaseResponse;
import com.memoryseed.backend.domain.shop.dto.ShopItemResponse;
import com.memoryseed.backend.domain.shop.service.ShopService;
import com.memoryseed.backend.global.response.Response;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequiredArgsConstructor
@RequestMapping("/api/shop")
public class ShopController {

    private final ShopService shopService;

    @GetMapping("/items")
    public ResponseEntity<Response<List<ShopItemResponse>>> getShopItems(
            @RequestHeader("X-USER-ID") Long userId
    ) {
        List<ShopItemResponse> shopItems = shopService.listShopItemsWithPurchaseStatus(userId);
        return ResponseEntity.ok(Response.success(shopItems));
    }

    @PostMapping("/purchase")
    public ResponseEntity<Response<PurchaseResponse>> purchaseItem(
            @RequestHeader("X-USER-ID") Long userId,
            @Valid @RequestBody PurchaseRequest req
    ) {
        PurchaseResponse purchaseResponse = shopService.purchase(userId, req);
        return ResponseEntity.status(HttpStatus.CREATED).body(Response.success(purchaseResponse));
    }
}