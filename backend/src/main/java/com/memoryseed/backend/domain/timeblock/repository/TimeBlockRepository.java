package com.memoryseed.backend.domain.timeblock.repository;

import com.memoryseed.backend.domain.timeblock.entity.TimeBlock;
import com.memoryseed.backend.domain.timeblock.entity.TimeBlockType;
import com.memoryseed.backend.domain.user.entity.User;
import org.springframework.data.jpa.repository.JpaRepository;

import java.time.LocalDateTime;
import java.util.List;

public interface TimeBlockRepository extends JpaRepository<TimeBlock, Long> {
    List<TimeBlock> findByUserAndStartTimeBetweenOrderByStartTimeAsc(User user, LocalDateTime start, LocalDateTime end);
    List<TimeBlock> findByUserAndTypeAndStartTimeBetweenOrderByStartTimeAsc(User user, TimeBlockType type, LocalDateTime start, LocalDateTime end);
}