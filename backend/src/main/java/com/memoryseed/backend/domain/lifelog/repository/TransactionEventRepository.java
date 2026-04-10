package com.memoryseed.backend.domain.lifelog.repository;

import com.memoryseed.backend.domain.lifelog.entity.TransactionEvent;
import com.memoryseed.backend.domain.user.entity.User;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.time.LocalDateTime;

public interface TransactionEventRepository extends JpaRepository<TransactionEvent, Long> {
    List<TransactionEvent> findByRunId(Long runId);
    List<TransactionEvent> findByUserAndTimestampBetween(User user, LocalDateTime start, LocalDateTime end);
}
