package com.memoryseed.backend.domain.quest.dto;

import com.memoryseed.backend.domain.quest.entity.QuestStatus;
import com.memoryseed.backend.domain.quest.entity.UserQuest;

import java.time.temporal.ChronoUnit;

public record QuestResponse(
        Long id,
        String text,             // 프론트의 text 매핑
        boolean isDone,          // 프론트의 isDone 매핑
        int coinReward,          // 프론트의 coinReward 매핑
        int affinityReward,      // 프론트의 affinityReward 매핑
        String type,             // 프론트의 type 매핑
        String period,           // 프론트의 period 매핑
        int targetValue          // 프론트의 targetValue 매핑
) {
    public static QuestResponse from(UserQuest userQuest) {
        String displayTitle = userQuest.getCustomTitle() != null ? userQuest.getCustomTitle() : userQuest.getTemplate().getTitle();
        int displayTargetValue = userQuest.getCustomTargetValue() != null ? userQuest.getCustomTargetValue() : userQuest.getTemplate().getTargetValue();

        // 날짜 차이 계산으로 period("daily" 또는 "weekly") 판별
        long daysBetween = ChronoUnit.DAYS.between(userQuest.getAssignedDate(), userQuest.getDueDate());
        String period = (daysBetween >= 7) ? "weekly" : "daily";
        // 수동 퀘스트인지 시스템 퀘스트인지 판별 (카테고리 소문자 변환 등 프론트 요청에 맞춤)
        String type = userQuest.getTemplate().getCategory().name().toLowerCase();

        return new QuestResponse(
                userQuest.getId(),
                displayTitle,
                userQuest.getStatus() == QuestStatus.DONE, // status가 DONE이면 true
                userQuest.getTemplate().getRewardCoin(),
                userQuest.getTemplate().getAffinityReward(),
                type,
                period,
                displayTargetValue
        );
    }
}