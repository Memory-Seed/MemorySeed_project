package com.memoryseed.backend.domain.quest.repository;

import com.memoryseed.backend.domain.quest.entity.QuestTemplate;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;

public interface QuestTemplateRepository extends JpaRepository<QuestTemplate, Long> {
    Optional<QuestTemplate> findByCode(String code);
}
