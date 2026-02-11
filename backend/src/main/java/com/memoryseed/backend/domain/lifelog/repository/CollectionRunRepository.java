package com.memoryseed.backend.domain.lifelog.repository;

import com.memoryseed.backend.domain.lifelog.entity.CollectionRun;
import com.memoryseed.backend.domain.user.entity.User;
import org.springframework.data.jpa.repository.JpaRepository;

import java.time.LocalDateTime;
import java.util.Optional;

public interface CollectionRunRepository extends JpaRepository<CollectionRun, Long> {

    // 특정 기간에서 "가장 최신 run" 하나 뽑기 (summary용)
    Optional<CollectionRun> findTopByUserAndRunAtBetweenOrderByRunAtDesc(
            User user,
            LocalDateTime startInclusive,
            LocalDateTime endExclusive
    );
}
