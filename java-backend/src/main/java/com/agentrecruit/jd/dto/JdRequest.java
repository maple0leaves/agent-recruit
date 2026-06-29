package com.agentrecruit.jd.dto;

import jakarta.validation.constraints.NotBlank;

/** 创建/更新 JD 的入参，对应 Python JDSchema。 */
public record JdRequest(
        @NotBlank(message = "职位名称不能为空") String title,
        String department,
        String skills,
        Integer experience_years,
        String education,
        Integer salary_min,
        Integer salary_max,
        String description) {

    public String departmentOrEmpty() {
        return department == null ? "" : department;
    }

    public String skillsOrEmpty() {
        return skills == null ? "" : skills;
    }

    public int experienceYearsOrZero() {
        return experience_years == null ? 0 : experience_years;
    }

    public String educationOrDefault() {
        return (education == null || education.isBlank()) ? "不限" : education;
    }

    public int salaryMinOrZero() {
        return salary_min == null ? 0 : salary_min;
    }

    public int salaryMaxOrZero() {
        return salary_max == null ? 0 : salary_max;
    }

    public String descriptionOrEmpty() {
        return description == null ? "" : description;
    }
}
