package com.memoryseed.backend.domain.quest.dto;

import com.memoryseed.backend.domain.quest.entity.QuestCategory;
import com.memoryseed.backend.domain.quest.entity.QuestStatus;
import com.memoryseed.backend.domain.quest.entity.UserQuest;

import java.time.LocalDate;

public record QuestResponse(
        Long id,
        String title,
        String description,
        QuestCategory category,
        Integer rewardCoin,
        QuestStatus status,
        LocalDate assignedDate,
        LocalDate dueDate
) {
    public static QuestResponse from(UserQuest userQuest) {
        String displayTitle = userQuest.getCustomTitle() != null ? userQuest.getCustomTitle() : userQuest.getTemplate().getTitle();
        String displayDescription = userQuest.getCustomDescription() != null ? userQuest.getCustomDescription() : userQuest.getTemplate().getDescription();

        return new QuestResponse(
                userQuest.getId(),
                displayTitle,
                displayDescription,
                userQuest.getTemplate().getCategory(),
                userQuest.getTemplate().getRewardCoin(),
                userQuest.getStatus(),
                userQuest.getAssignedDate(),
                userQuest.getDueDate()
        );
    }
}
