package com.memoryseed.backend.domain.quest.service;

import com.memoryseed.backend.domain.quest.dto.QuestCreateRequest;
import com.memoryseed.backend.domain.quest.dto.QuestResponse;
import com.memoryseed.backend.domain.quest.entity.QuestStatus;
import com.memoryseed.backend.domain.quest.entity.QuestTemplate;
import com.memoryseed.backend.domain.quest.entity.UserQuest;
import com.memoryseed.backend.domain.quest.repository.QuestTemplateRepository;
import com.memoryseed.backend.domain.quest.repository.UserQuestRepository;
import com.memoryseed.backend.domain.user.entity.User;
import com.memoryseed.backend.domain.user.repository.UserRepository;
import com.memoryseed.backend.domain.wallet.entity.UserWallet;
import com.memoryseed.backend.domain.wallet.repository.UserWalletRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDate;
import java.util.List;
import java.util.UUID;

@Service
@Transactional
@RequiredArgsConstructor
public class QuestService {

    private final UserRepository userRepository;
    private final UserQuestRepository userQuestRepository;
    private final QuestTemplateRepository questTemplateRepository;
    private final UserWalletRepository userWalletRepository;

    private static final int USER_CREATED_QUEST_REWARD = 10; // 사용자 생성 퀘스트 고정 보상

    public QuestResponse createQuest(Long userId, QuestCreateRequest request) {
        User user = userRepository.findById(userId)
                .orElseThrow(() -> new IllegalArgumentException("User not found"));

        // 사용자 생성 퀘스트를 위한 동적 QuestTemplate 생성
        QuestTemplate template = new QuestTemplate(
                "USER_" + UUID.randomUUID(), // 유니크 코드 생성
                request.title(),
                request.description(),
                request.category(),
                USER_CREATED_QUEST_REWARD
        );
        questTemplateRepository.save(template);

        UserQuest userQuest = new UserQuest(user, template, LocalDate.now(), LocalDate.now().plusDays(1));
        userQuestRepository.save(userQuest);

        return QuestResponse.from(userQuest);
    }

    @Transactional(readOnly = true)
    public List<QuestResponse> getActiveQuests(Long userId) {
        return userQuestRepository.findByUserIdAndStatusWithTemplate(userId, QuestStatus.ASSIGNED)
                .stream()
                .map(QuestResponse::from)
                .toList();
    }

    public QuestResponse completeQuest(Long userId, Long questId) {
        User user = userRepository.findById(userId)
                .orElseThrow(() -> new IllegalArgumentException("User not found"));

        UserQuest userQuest = userQuestRepository.findById(questId)
                .orElseThrow(() -> new IllegalArgumentException("Quest not found"));

        if (!userQuest.getUser().getId().equals(userId)) {
            throw new IllegalStateException("This quest does not belong to the user");
        }

        if (userQuest.getStatus() != QuestStatus.ASSIGNED) {
            throw new IllegalStateException("Quest is not in ASSIGNED status");
        }

        userQuest.completeNow();

        // 보상 지급
        if (!userQuest.getRewardGranted()) {
            UserWallet wallet = userWalletRepository.findByUser(user)
                    .orElseGet(() -> {
                        UserWallet newWallet = new UserWallet(user);
                        return userWalletRepository.save(newWallet);
                    });

            int reward = userQuest.getTemplate().getRewardCoin();
            wallet.addCoins(reward);
            userQuest.markRewardGranted();
        }

        return QuestResponse.from(userQuest);
    }
}
