package com.memoryseed.backend.domain.lifelog.entity;

import com.memoryseed.backend.domain.user.entity.User;
import com.memoryseed.backend.global.entity.BaseTimeEntity;
import jakarta.persistence.*;

import java.time.LocalDateTime;

@Entity
@Table(
        name = "weather_timeseries",
        indexes = {
                @Index(name="idx_weather_user_time", columnList="user_id, time")
        }
)
public class WeatherTimeseries extends BaseTimeEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name="user_id", nullable = false)
    private User user;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name="run_id", nullable = false)
    private CollectionRun run;

    @Column(nullable = false)
    private LocalDateTime time;

    @Column(nullable = false)
    private Double temperatureC;

    private Integer pm10;

    @Column(length = 50)
    private String condition;

    protected WeatherTimeseries() {}

    public WeatherTimeseries(User user, CollectionRun run, LocalDateTime time,
                             Double temperatureC, Integer pm10, String condition) {
        this.user = user;
        this.run = run;
        this.time = time;
        this.temperatureC = temperatureC;
        this.pm10 = pm10;
        this.condition = condition;
    }

    public Long getId() { return id; }
    public User getUser() { return user; }
    public CollectionRun getRun() { return run; }
    public LocalDateTime getTime() { return time; }
    public Double getTemperatureC() { return temperatureC; }
    public Integer getPm10() { return pm10; }
    public String getCondition() { return condition; }
}
