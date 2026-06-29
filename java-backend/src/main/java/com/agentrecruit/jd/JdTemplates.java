package com.agentrecruit.jd;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/** 硬编码 JD 模板，对应 Python backend/config/templates.py。 */
public final class JdTemplates {

    private JdTemplates() {
    }

    public static List<Map<String, Object>> all() {
        return List.of(
                template("软件工程师",
                        "Java, Python, Spring Boot, FastAPI, React, TypeScript, SQL, MySQL, Redis, Docker, Kubernetes, Git, RESTful API, 微服务, Linux, 单元测试, CI/CD, 性能优化",
                        3, "本科",
                        15000, 30000,
                        "负责核心业务系统研发，覆盖后端服务、前端页面、数据库优化、接口联调、测试发布和线上稳定性建设。"),
                template("产品经理",
                        "Axure, Figma, PRD, 用户调研, 需求分析, 数据分析, SQL, 原型设计, 竞品分析, A/B测试, Jira, Scrum, 用户故事, 指标体系, Roadmap, 跨部门沟通, 上线复盘",
                        2, "本科",
                        12000, 25000,
                        "负责 B 端产品从需求洞察、方案设计到上线复盘的全流程，协调研发、设计、运营和销售团队推进交付。"),
                template("销售经理",
                        "商务谈判, CRM, 方案制作, 客户管理, 大客户销售, 线索管理, 渠道拓展, 招投标, 合同谈判, 回款跟进, 销售预测, 客户成功, 行业洞察, 数据复盘, 演示汇报, 续约增长",
                        3, "大专",
                        10000, 20000,
                        "负责企业客户开拓、商机推进、方案演示、合同谈判和客户关系维护，推动销售目标达成与续约增长。"));
    }

    private static Map<String, Object> template(String name, String skills, int years, String education,
                                                int salaryMin, int salaryMax, String description) {
        Map<String, Object> map = new LinkedHashMap<>();
        map.put("name", name);
        map.put("description", description);
        map.put("skills", skills);
        map.put("experience_years", years);
        map.put("education", education);
        map.put("salary_min", salaryMin);
        map.put("salary_max", salaryMax);
        return map;
    }
}
