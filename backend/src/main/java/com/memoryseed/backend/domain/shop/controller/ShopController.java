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
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequiredArgsConstructor
@RequestMapping("/api/shop")
public class ShopController {

    private final ShopService shopService;

    @GetMapping("/items")
    public ResponseEntity<Response<List<ShopItemResponse>>> getShopItems(
            Authentication authentication
    ) {
        String providerId = authentication.getName();
        List<ShopItemResponse> shopItems = shopService.listShopItemsWithPurchaseStatus(providerId);
        return ResponseEntity.ok(Response.success(shopItems));
    }

    @PostMapping("/purchase")
    public ResponseEntity<Response<PurchaseResponse>> purchaseItem(
            Authentication authentication,
            @Valid @RequestBody PurchaseRequest req
    ) {
        String providerId = authentication.getName();
        PurchaseResponse purchaseResponse = shopService.purchase(providerId, req);
        return ResponseEntity.status(HttpStatus.CREATED).body(Response.success(purchaseResponse));
    }
}