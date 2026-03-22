package com.memoryseed.backend.domain.quest.scheduler;

import com.memoryseed.backend.domain.quest.entity.QuestStatus;
import com.memoryseed.backend.domain.quest.entity.UserQuest;
import com.memoryseed.backend.domain.quest.repository.UserQuestRepository;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDate;
import java.util.List;

@Component
public class QuestScheduler {

    private final UserQuestRepository userQuestRepository;

    public QuestScheduler(UserQuestRepository userQuestRepository) {
        this.userQuestRepository = userQuestRepository;
    }

    // 매일 자정(00:00:00)에 실행
    @Scheduled(cron = "0 0 0 * * *")
    @Transactional
    public void handleExpiredQuests() {
        // 엔티티 타입에 맞게 LocalDate.now() 사용!
        List<UserQuest> expiredQuests = userQuestRepository.findByStatusAndDueDateBefore(
                QuestStatus.ASSIGNED, LocalDate.now()
        );

        for (UserQuest quest : expiredQuests) {
            quest.changeStatus(QuestStatus.SKIPPED);
        }

        if (!expiredQuests.isEmpty()) {
            System.out.println("[Scheduler] 마감일이 지난 퀘스트 " + expiredQuests.size() + "개를 FAILED 처리했습니다.");
        }
    }
}