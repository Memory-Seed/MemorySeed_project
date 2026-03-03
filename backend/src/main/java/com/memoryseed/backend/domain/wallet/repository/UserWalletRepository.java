package com.memoryseed.backend.domain.wallet.repository;

import com.memoryseed.backend.domain.wallet.entity.UserWallet;
import org.springframework.data.jpa.repository.JpaRepository;

public interface UserWalletRepository extends JpaRepository<UserWallet, Long> {
}