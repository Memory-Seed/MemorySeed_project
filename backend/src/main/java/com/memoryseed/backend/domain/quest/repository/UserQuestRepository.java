package com.memoryseed.backend.domain.quest.repository;

import com.memoryseed.backend.domain.quest.entity.QuestStatus;
import com.memoryseed.backend.domain.quest.entity.UserQuest;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;

import java.util.List;

public interface UserQuestRepository extends JpaRepository<UserQuest, Long> {
    @Query("select uq from UserQuest uq join fetch uq.template where uq.user.id = :userId and uq.status = :status")
    List<UserQuest> findByUserIdAndStatusWithTemplate(Long userId, QuestStatus status);
}
