package com.memoryseed.backend.domain.quest.repository;

import com.memoryseed.backend.domain.quest.entity.QuestStatus;
import com.memoryseed.backend.domain.quest.entity.UserQuest;
import com.memoryseed.backend.domain.user.entity.User;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;

import java.time.LocalDate;
import java.util.List;

public interface UserQuestRepository extends JpaRepository<UserQuest, Long> {
    @Query("select uq from UserQuest uq join fetch uq.template where uq.user = :user and uq.status = :status")
    List<UserQuest> findByUserAndStatusWithTemplate(User user, QuestStatus status);
    List<UserQuest> findByStatusAndDueDateBefore(QuestStatus status, LocalDate now);
}
