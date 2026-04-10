package com.memoryseed.backend.domain.lifelog.repository;

import com.memoryseed.backend.domain.lifelog.entity.UserCalendar;
import com.memoryseed.backend.domain.user.entity.User;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface UserCalendarRepository extends JpaRepository<UserCalendar, Long> {
    List<UserCalendar> findByUser(User user);
}