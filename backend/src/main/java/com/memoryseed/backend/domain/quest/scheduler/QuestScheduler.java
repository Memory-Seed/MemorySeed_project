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
        System.out.println("⏰ [Scheduler] 스케줄러 작동 시작 - " + LocalDate.now() + " 기준");

        List<UserQuest> expiredQuests = userQuestRepository.findByStatusAndDueDateBefore(
                QuestStatus.ASSIGNED, LocalDate.now()
        );

        // 검색된 개수를 무조건 출력하게 설정! (0개면 0개라고 뜰 겁니다)
        System.out.println("🔍 [Scheduler] 조건에 맞는 퀘스트 개수: " + expiredQuests.size());

        for (UserQuest quest : expiredQuests) {
            quest.changeStatus(QuestStatus.SKIPPED);
        }

        if (!expiredQuests.isEmpty()) {
            System.out.println("✅ [Scheduler] 총 " + expiredQuests.size() + "개를 SKIPPED 처리 완료!");
        }
    }
}