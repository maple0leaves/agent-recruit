package com.agentrecruit.jd.dto;

import com.fasterxml.jackson.annotation.JsonFormat;
import com.agentrecruit.jd.entity.Jd;

import java.time.LocalDateTime;

/** 单个 JD 输出，字段名与 Python JDResponse 一致（snake_case）。 */
public record JdResponse(
        Long id,
        String title,
        String department,
        String skills,
        Integer experience_years,
        String education,
        Integer salary_min,
        Integer salary_max,
        String description,
        String status,
        @JsonFormat(shape = JsonFormat.Shape.STRING) LocalDateTime created_at,
        @JsonFormat(shape = JsonFormat.Shape.STRING) LocalDateTime updated_at) {

    public static JdResponse from(Jd jd) {
        return new JdResponse(
                jd.getId(),
                jd.getTitle(),
                jd.getDepartment(),
                jd.getSkills(),
                jd.getExperienceYears(),
                jd.getEducation(),
                jd.getSalaryMin(),
                jd.getSalaryMax(),
                jd.getDescription(),
                jd.getStatus(),
                jd.getCreatedAt(),
                jd.getUpdatedAt());
    }
}
