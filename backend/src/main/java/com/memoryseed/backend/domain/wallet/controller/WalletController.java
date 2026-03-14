package com.memoryseed.backend.domain.wallet.controller;

import com.memoryseed.backend.domain.wallet.dto.WalletResponse;
import com.memoryseed.backend.domain.wallet.service.WalletService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/wallet")
public class WalletController {

    private final WalletService walletService;

    public WalletController(WalletService walletService) {
        this.walletService = walletService;
    }

    @GetMapping
    public ResponseEntity<WalletResponse> get(
            @RequestHeader("X-USER-ID") Long userId
    ) {
        return ResponseEntity.ok(walletService.getWallet(userId));
    }
}