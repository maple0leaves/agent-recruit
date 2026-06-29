package com.agentrecruit.match.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@TableName("match_sessions")
public class MatchSession {

    @TableId(type = IdType.AUTO)
    private Long id;

    private Long jdId;
    private Long candidateId;
    private String threadId;
    private String status;
    private Integer totalCandidates;
    private Integer approvedCount;
    private Integer rejectedCount;
    private String resultsJson;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}
