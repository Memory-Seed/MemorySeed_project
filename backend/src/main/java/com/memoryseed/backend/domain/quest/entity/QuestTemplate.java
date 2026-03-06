package com.memoryseed.backend.domain.quest.entity;

import com.memoryseed.backend.global.entity.BaseTimeEntity;
import jakarta.persistence.*;
import lombok.AccessLevel;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Entity
@Table(
        name = "quest_templates",
        uniqueConstraints = @UniqueConstraint(name = "uk_quest_template_code", columnNames = "code"),
        indexes = @Index(name = "idx_quest_template_active", columnList = "active")
)
@Getter
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class QuestTemplate extends BaseTimeEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(length = 50, nullable = false, unique = true)
    private String code;

    @Column(length = 100, nullable = false)
    private String title;

    @Column(columnDefinition = "TEXT")
    private String description;

    @Enumerated(EnumType.STRING)
    @Column(length = 30, nullable = false)
    private QuestCategory category;

    @Column(nullable = false)
    private Integer rewardCoin = 0;

    @Column(nullable = false)
    private Boolean active = true;

    public QuestTemplate(String code, String title, String description, QuestCategory category, int rewardCoin) {
        this.code = code;
        this.title = title;
        this.description = description;
        this.category = category;
        this.rewardCoin = rewardCoin;
        this.active = true;
    }

    public void deactivate() {
        this.active = false;
    }
}