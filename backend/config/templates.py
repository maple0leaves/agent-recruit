"""Hardcoded JD templates for quick creation (D-09, D-10)."""
from typing import TypedDict


class JDTemplate(TypedDict):
    """Schema for a JD template visible to HR for quick creation."""
    name: str
    description: str
    skills: str
    experience_years: int
    education: str
    salary_min: int
    salary_max: int


TEMPLATES: list[JDTemplate] = [
    {
        "name": "软件工程师",
        "description": "负责核心业务系统研发，覆盖后端服务、前端页面、数据库优化、接口联调、测试发布和线上稳定性建设。",
        "skills": "Java, Python, Spring Boot, FastAPI, React, TypeScript, SQL, MySQL, Redis, Docker, Kubernetes, Git, RESTful API, 微服务, Linux, 单元测试, CI/CD, 性能优化",
        "experience_years": 3,
        "education": "本科",
        "salary_min": 15000,
        "salary_max": 30000,
    },
    {
        "name": "产品经理",
        "description": "负责 B 端产品从需求洞察、方案设计到上线复盘的全流程，协调研发、设计、运营和销售团队推进交付。",
        "skills": "Axure, Figma, PRD, 用户调研, 需求分析, 数据分析, SQL, 原型设计, 竞品分析, A/B测试, Jira, Scrum, 用户故事, 指标体系, Roadmap, 跨部门沟通, 上线复盘",
        "experience_years": 2,
        "education": "本科",
        "salary_min": 12000,
        "salary_max": 25000,
    },
    {
        "name": "销售经理",
        "description": "负责企业客户开拓、商机推进、方案演示、合同谈判和客户关系维护，推动销售目标达成与续约增长。",
        "skills": "商务谈判, CRM, 方案制作, 客户管理, 大客户销售, 线索管理, 渠道拓展, 招投标, 合同谈判, 回款跟进, 销售预测, 客户成功, 行业洞察, 数据复盘, 演示汇报, 续约增长",
        "experience_years": 3,
        "education": "大专",
        "salary_min": 10000,
        "salary_max": 20000,
    },
]
