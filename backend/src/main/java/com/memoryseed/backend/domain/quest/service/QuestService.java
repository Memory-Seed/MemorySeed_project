package com.memoryseed.backend.domain.quest.service;

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
    private static final int MANUAL_QUEST_REWARD = 10;
    private static final int AI_QUEST_REWARD = 15;

    // 1. 사용자 직접 생성 로직
    public QuestResponse createCustomQuest(Long userId, QuestCreateRequest request) {
        User user = getUser(userId);
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

        // 2. AI 추천 퀘스트 생성 로직
    public QuestResponse createAiQuest(Long userId, AiQuestCreateRequest request) {
        User user = getUser(userId);
        QuestTemplate template = getOrCreateGenericTemplate("AI_QUEST", "AI 추천 퀘스트", request.category(), AI_QUEST_REWARD);
       // TODO: 외부 AI API(OpenAI, Gemini 등) 호출 로직 구현 위치
       // 임시 Mock 데이터 (추후 AI 응답값으로 대체)
        String aiGeneratedTitle = "[AI 추천] " + request.category().name() + " 마스터하기!";
        String aiGeneratedDesc = "AI가 유저의 최근 활동을 분석하여 추천하는 맞춤형 퀘스트입니다.";

        UserQuest userQuest = new UserQuest(
                user,
                template,
                LocalDate.now(),
                LocalDate.now().plusDays(1),
                aiGeneratedTitle,
                aiGeneratedDesc,
                1 // 임시 목표 수치 (나중에 AI가 주는 값으로 교체)
        );
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

    // --- 헬퍼 메서드 ---
    private User getUser(Long userId) {
        return userRepository.findById(userId)
                .orElseThrow(() -> new IllegalArgumentException("User not found"));
    }

    private QuestTemplate getOrCreateGenericTemplate(String code, String defaultTitle, QuestCategory category, int rewardCoin) {
        return questTemplateRepository.findByCode(code)
                .orElseGet(() -> questTemplateRepository.save(
                        new QuestTemplate(
                                code,
                                defaultTitle,
                                "시스템 기본 템플릿",
                                category,
                                rewardCoin,
                                5, // affinityReward (기본값)
                                1  // targetValue (기본값)
                        )
                ));
    }
}