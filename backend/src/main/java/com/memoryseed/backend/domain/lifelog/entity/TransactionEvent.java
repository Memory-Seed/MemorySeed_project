package com.memoryseed.backend.domain.lifelog.entity;

import com.memoryseed.backend.domain.user.entity.User;
import com.memoryseed.backend.global.entity.BaseTimeEntity;
import jakarta.persistence.*;

import java.time.LocalDateTime;

@Entity
@Table(
        name = "transaction_events",
        indexes = {
                @Index(name="idx_tx_user_time", columnList="user_id, timestamp")
        }
)
public class TransactionEvent extends BaseTimeEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name="user_id", nullable = false)
    private User user;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name="run_id", nullable = false)
    private CollectionRun run;

    @Column(nullable = false)
    private LocalDateTime timestamp;

    @Column(nullable = false)
    private Integer amountKrw;

    @Column(length = 100)
    private String merchant;

    @Column(columnDefinition = "TEXT")
    private String rawMessage;

    protected TransactionEvent() {}

    public TransactionEvent(User user, CollectionRun run, LocalDateTime timestamp,
                            Integer amountKrw, String merchant, String rawMessage) {
        this.user = user;
        this.run = run;
        this.timestamp = timestamp;
        this.amountKrw = amountKrw;
        this.merchant = merchant;
        this.rawMessage = rawMessage;
    }

    public Long getId() { return id; }
    public User getUser() { return user; }
    public CollectionRun getRun() { return run; }
    public LocalDateTime getTimestamp() { return timestamp; }
    public Integer getAmountKrw() { return amountKrw; }
    public String getMerchant() { return merchant; }
    public String getRawMessage() { return rawMessage; }
}
