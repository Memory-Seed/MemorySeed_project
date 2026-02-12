package com.memoryseed.backend.domain.lifelog.repository;

import com.memoryseed.backend.domain.lifelog.entity.ScreenTimeSession;
import org.springframework.data.jpa.repository.JpaRepository;

public interface ScreenTimeSessionRepository extends JpaRepository<ScreenTimeSession, Long> { }
