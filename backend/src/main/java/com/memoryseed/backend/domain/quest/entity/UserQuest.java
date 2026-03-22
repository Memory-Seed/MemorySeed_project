package com.memoryseed.backend.domain.quest.entity;

import com.memoryseed.backend.domain.user.entity.User;
import com.memoryseed.backend.global.entity.BaseTimeEntity;
import jakarta.persistence.*;
import lombok.AccessLevel;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.time.LocalDate;
import java.time.LocalDateTime;

@Entity
@Table(
        name = "user_quests",
        uniqueConstraints = @UniqueConstraint(name = "uk_user_quest_day", columnNames = {"user_id", "template_id", "assigned_date"}),
        indexes = {
                @Index(name = "idx_user_quest_status", columnList = "user_id,status"),
                @Index(name = "idx_user_quest_assigned", columnList = "user_id,assigned_date")
        }
)
@Getter
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class UserQuest extends BaseTimeEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "user_id", nullable = false)
    private User user;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "template_id", nullable = false)
    private QuestTemplate template;

    @Column(name = "assigned_date", nullable = false)
    private LocalDate assignedDate;

    @Column(name = "due_date")
    private LocalDate dueDate;

    @Enumerated(EnumType.STRING)
    @Column(length = 20, nullable = false)
    private QuestStatus status = QuestStatus.ASSIGNED;

    public void changeStatus(QuestStatus newStatus) {
        this.status = newStatus;
    }

    private LocalDateTime completedAt;

    @Column(nullable = false)
    private Boolean rewardGranted = false;

    @Column(length = 100)
    private String customTitle;

    @Column(columnDefinition = "TEXT")
    private String customDescription;

    @Column
    private Integer customTargetValue;

    public UserQuest(User user, QuestTemplate template, LocalDate assignedDate, LocalDate dueDate, String customTitle, String customDescription, Integer customTargetValue) {
        this.user = user;
        this.template = template;
        this.assignedDate = assignedDate;
        this.dueDate = dueDate;
        this.status = QuestStatus.ASSIGNED;
        this.rewardGranted = false;
        this.customTitle = customTitle;
        this.customDescription = customDescription;
        this.customTargetValue = customTargetValue;
    }

    public void completeNow() {
        this.status = QuestStatus.DONE;
        this.completedAt = LocalDateTime.now();
    }

    public void markRewardGranted() {
        this.rewardGranted = true;
    }
}