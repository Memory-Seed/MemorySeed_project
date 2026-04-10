package com.memoryseed.backend.domain.wallet.service;

import com.memoryseed.backend.domain.user.entity.User;
import com.memoryseed.backend.domain.user.repository.UserRepository;
import com.memoryseed.backend.domain.wallet.dto.WalletResponse;
import com.memoryseed.backend.domain.wallet.entity.UserWallet;
import com.memoryseed.backend.domain.wallet.repository.UserWalletRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class WalletService {

    private final UserRepository userRepository;
    private final UserWalletRepository walletRepository;

    public WalletService(UserRepository userRepository, UserWalletRepository walletRepository) {
        this.userRepository = userRepository;
        this.walletRepository = walletRepository;
    }

    @Transactional(readOnly = true)
    public WalletResponse getWallet(String providerId) {
        User user = userRepository.findByProviderId(providerId)
                .orElseThrow(() -> new IllegalArgumentException("user not found: " + providerId));

        UserWallet wallet = walletRepository.findById(user.getId())
                .orElseGet(() -> walletRepository.save(new UserWallet(user)));

        return new WalletResponse(wallet.getCoinBalance());
    }
}