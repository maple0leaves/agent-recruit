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
        "description": "前后端全栈开发工程师",
        "skills": "Java, Python, SQL, React, Docker, Git",
        "experience_years": 3,
        "education": "本科",
        "salary_min": 15000,
        "salary_max": 30000,
        "description": "负责公司核心产品的功能开发与维护，包括后端API设计、前端页面开发、数据库优化等工作。",
    },
    {
        "name": "产品经理",
        "description": "B端产品规划与设计",
        "skills": "Axure, Figma, SQL, 用户调研, 数据分析",
        "experience_years": 2,
        "education": "本科",
        "salary_min": 12000,
        "salary_max": 25000,
        "description": "负责产品需求分析、原型设计、项目跟进、跨部门协调等工作。",
    },
    {
        "name": "销售经理",
        "description": "企业客户销售与关系维护",
        "skills": "商务谈判, CRM, 方案制作, 客户管理",
        "experience_years": 3,
        "education": "大专",
        "salary_min": 10000,
        "salary_max": 20000,
        "description": "负责开拓和维护企业客户，制定销售策略，完成业绩指标。",
    },
]
