package com.agentrecruit.jd.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@TableName("jds")
public class Jd {

    @TableId(type = IdType.AUTO)
    private Long id;

    private String title;
    private String department;
    private String skills;
    private Integer experienceYears;
    /** 高中/大专/本科/硕士/博士/不限 */
    private String education;
    private Integer salaryMin;
    private Integer salaryMax;
    private String description;
    /** draft | active | closed */
    private String status;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}
