package com.memoryseed.backend.domain.wallet.entity;

import com.memoryseed.backend.domain.user.entity.User;
import com.memoryseed.backend.global.entity.BaseTimeEntity;
import jakarta.persistence.*;
import lombok.AccessLevel;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Entity
@Table(name = "user_wallets")
@Getter
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class UserWallet extends BaseTimeEntity {

    @Id
    @Column(name = "user_id")
    private Long userId;

    @MapsId
    @OneToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "user_id")
    private User user;

    @Column(nullable = false)
    private Integer coinBalance = 0;

    public UserWallet(User user) {
        this.user = user;
        this.coinBalance = 0;
    }

    public void addCoins(int amount) {
        if (amount < 0) throw new IllegalArgumentException("amount must be >= 0");
        this.coinBalance += amount;
    }

    public void subtractCoins(int amount) {
        if (amount < 0) throw new IllegalArgumentException("amount must be >= 0");
        if (this.coinBalance < amount) throw new IllegalStateException("not enough coins");
        this.coinBalance -= amount;
    }
}