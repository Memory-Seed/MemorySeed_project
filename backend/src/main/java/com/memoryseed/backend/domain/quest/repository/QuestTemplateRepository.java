package com.memoryseed.backend.domain.quest.repository;

import com.memoryseed.backend.domain.quest.entity.QuestTemplate;
import org.springframework.data.jpa.repository.JpaRepository;

public interface QuestTemplateRepository extends JpaRepository<QuestTemplate, Long> {
}
