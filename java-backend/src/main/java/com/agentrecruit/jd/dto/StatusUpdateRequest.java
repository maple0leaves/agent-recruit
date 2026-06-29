package com.agentrecruit.jd.dto;

import jakarta.validation.constraints.NotBlank;

public record StatusUpdateRequest(@NotBlank(message = "状态不能为空") String status) {
}
