package com.memoryseed.backend.domain.timeblock.service;

import com.memoryseed.backend.domain.timeblock.dto.TimeBlockCreateRequest;
import com.memoryseed.backend.domain.timeblock.dto.TimeBlockResponse;
import com.memoryseed.backend.domain.timeblock.entity.TimeBlock;
import com.memoryseed.backend.domain.timeblock.entity.TimeBlockType;
import com.memoryseed.backend.domain.timeblock.repository.TimeBlockRepository;
import com.memoryseed.backend.domain.user.entity.User;
import com.memoryseed.backend.domain.user.repository.UserRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.List;

@Service
public class TimeBlockService {

    private final UserRepository userRepository;
    private final TimeBlockRepository timeBlockRepository;

    public TimeBlockService(UserRepository userRepository, TimeBlockRepository timeBlockRepository) {
        this.userRepository = userRepository;
        this.timeBlockRepository = timeBlockRepository;
    }

    @Transactional
    public TimeBlockResponse create(String providerId, TimeBlockCreateRequest req) {
        User user = userRepository.findByProviderId(providerId)
                .orElseThrow(() -> new IllegalArgumentException("User not found with providerId: " + providerId));

        TimeBlock tb = new TimeBlock(user, req.startTime(), req.endTime(), req.type());
        timeBlockRepository.save(tb);
        return TimeBlockResponse.from(tb);
    }

    @Transactional(readOnly = true)
    public List<TimeBlockResponse> list(String providerId, LocalDate from, LocalDate to, TimeBlockType type) {
        User user = userRepository.findByProviderId(providerId)
                .orElseThrow(() -> new IllegalArgumentException("User not found with providerId: " + providerId));

        LocalDateTime start = from.atStartOfDay();
        LocalDateTime end = to.plusDays(1).atStartOfDay();

        List<TimeBlock> blocks = (type == null)
                ? timeBlockRepository.findByUserAndStartTimeBetweenOrderByStartTimeAsc(user, start, end)
                : timeBlockRepository.findByUserAndTypeAndStartTimeBetweenOrderByStartTimeAsc(user, type, start, end);

        return blocks.stream().map(TimeBlockResponse::from).toList();
    }

    @Transactional
    public void delete(String providerId, Long timeBlockId) {
        User user = userRepository.findByProviderId(providerId)
                .orElseThrow(() -> new IllegalArgumentException("User not found with providerId: " + providerId));

        TimeBlock tb = timeBlockRepository.findById(timeBlockId)
                .orElseThrow(() -> new IllegalArgumentException("timeBlock not found: " + timeBlockId));

        if (!tb.getUser().getProviderId().equals(user.getProviderId())) {
            throw new IllegalStateException("not your timeBlock");
        }

        timeBlockRepository.delete(tb);
    }
}