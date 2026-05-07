package com.memoryseed.backend.domain.quest.service;

import com.memoryseed.backend.domain.ai.client.AiApiClient;
import com.memoryseed.backend.domain.lifelog.dto.LifelogRawResponse;
import com.memoryseed.backend.domain.lifelog.service.LifelogQueryService;
import com.memoryseed.backend.domain.quest.dto.AiQuestCreateRequest;
import com.memoryseed.backend.domain.quest.dto.QuestCreateRequest;
import com.memoryseed.backend.domain.quest.dto.QuestResponse;
import com.memoryseed.backend.domain.quest.entity.QuestCategory;
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
import java.util.ArrayList;
import java.util.List;
import java.util.NoSuchElementException;
import java.util.UUID;

@Service
@Transactional
@RequiredArgsConstructor
public class QuestService {

    private final UserRepository userRepository;
    private final UserQuestRepository userQuestRepository;
    private final QuestTemplateRepository questTemplateRepository;
    private final UserWalletRepository userWalletRepository;
    private final AiApiClient aiApiClient;
    private final LifelogQueryService lifelogQueryService;

    private static final int MANUAL_QUEST_REWARD = 10;
    private static final int AI_QUEST_REWARD = 20;

    // 1. 사용자 직접 생성 로직
    public QuestResponse createCustomQuest(String providerId, QuestCreateRequest request) {
        User user = getUser(providerId);
        QuestTemplate template = new QuestTemplate(
                "USER_" + java.util.UUID.randomUUID().toString(),
                request.title(),
                request.description(),
                request.category(),
                10, // 커스텀 퀘스트 보상 코인
                5,  // 호감도 보상 (고정값)
                request.targetValue() // 프론트가 보낸 목표 수치
        );
        questTemplateRepository.save(template);

        // UserQuest 생성자에 targetValue 추가
        UserQuest userQuest = new UserQuest(
                user,
                template,
                LocalDate.now(),
                request.dueDate(),
                request.title(),
                request.description(),
                request.targetValue()
        );
        userQuestRepository.save(userQuest);

        return QuestResponse.from(userQuest);
    }

    // 2. AI 추천 퀘스트 생성 로직 (다수 퀘스트 한 번에 저장)
    public List<QuestResponse> createAiQuests(String providerId, AiQuestCreateRequest request) {
        User user = getUser(providerId);

        // 오늘 lifelog 데이터 조회 (AI 분석용)
        LocalDate today = LocalDate.now();
        LifelogRawResponse lifelog = lifelogQueryService.getRawLifelogs(providerId, today, today);

        // AI 서버 호출
        List<AiApiClient.AiQuest> aiQuests = aiApiClient.recommendDaily(
                request.category().name(),
                request.diaryText(),
                today,
                lifelog
        );

        if (aiQuests.isEmpty()) {
            // AI 서버 미연결 시 fallback 단건 생성
            return List.of(saveFallbackQuest(user, request.category()));
        }

        // 모든 AI 퀘스트를 DB에 저장
        List<QuestResponse> responses = new ArrayList<>();
        for (AiApiClient.AiQuest aiQuest : aiQuests) {
            QuestTemplate template = new QuestTemplate(
                    "AI_" + UUID.randomUUID(),
                    aiQuest.text(),
                    aiQuest.description(),
                    parseCategory(aiQuest.type(), request.category()),
                    aiQuest.coinReward() != null ? aiQuest.coinReward() : AI_QUEST_REWARD,
                    aiQuest.affinityReward() != null ? aiQuest.affinityReward() : 5,
                    aiQuest.targetValue() != null ? aiQuest.targetValue() : 1,
                    aiQuest.difficulty() != null ? aiQuest.difficulty() : "NORMAL"
            );
            questTemplateRepository.save(template);

            UserQuest userQuest = new UserQuest(
                    user,
                    template,
                    today,
                    today.plusDays(1), // daily 고정
                    aiQuest.text(),
                    aiQuest.description(),
                    aiQuest.targetValue() != null ? aiQuest.targetValue() : 1
            );
            userQuestRepository.save(userQuest);
            responses.add(QuestResponse.from(userQuest));
        }
        return responses;
    }

    private QuestResponse saveFallbackQuest(User user, QuestCategory category) {
        QuestTemplate template = new QuestTemplate(
                "AI_" + UUID.randomUUID(),
                "[AI 추천] " + category.name() + " 챌린지",
                "AI 서버 미연결 - 임시 퀘스트입니다.",
                category,
                AI_QUEST_REWARD,
                5,
                1,
                "NORMAL"
        );
        questTemplateRepository.save(template);

        LocalDate today = LocalDate.now();
        UserQuest userQuest = new UserQuest(
                user, template, today, today.plusDays(1),
                template.getTitle(), template.getDescription(), 1
        );
        userQuestRepository.save(userQuest);
        return QuestResponse.from(userQuest);
    }

    private QuestCategory parseCategory(String type, QuestCategory fallback) {
        if (type == null) return fallback;
        try {
            return QuestCategory.valueOf(type.toUpperCase());
        } catch (IllegalArgumentException e) {
            return fallback;
        }
    }

    @Transactional(readOnly = true)
    public List<QuestResponse> getActiveQuests(String providerId) {
        User user = getUser(providerId);
        return userQuestRepository.findByUserAndStatusWithTemplate(user, QuestStatus.ASSIGNED)
                .stream()
                .map(QuestResponse::from)
                .toList();
    }

    public QuestResponse completeQuest(String providerId, Long questId) {
        User user = userRepository.findByProviderId(providerId)
                .orElseThrow(() -> new IllegalArgumentException("User not found with providerId: " + providerId));
        UserQuest userQuest = userQuestRepository.findById(questId)
                .orElseThrow(() -> new IllegalArgumentException("Quest not found"));

        if (!userQuest.getUser().getProviderId().equals(providerId)) {
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

    // --- 헬퍼 메서드 ---
    private User getUser(String providerId) {
        return userRepository.findByProviderId(providerId)
                .orElseThrow(() -> new IllegalArgumentException("User not found with providerId: " + providerId));
    }

    public void deleteQuest(String providerId, Long questId) {
        User user = getUser(providerId);
        com.memoryseed.backend.domain.quest.entity.UserQuest userQuest = userQuestRepository.findById(questId)
                .orElseThrow(() -> new NoSuchElementException("Quest not found with id: " + questId));

        if (!userQuest.getUser().getProviderId().equals(providerId)) {
            throw new IllegalArgumentException("Unauthorized: User does not own this quest.");
        }

        userQuestRepository.delete(userQuest);
    }
}