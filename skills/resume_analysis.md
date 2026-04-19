---
name: resume_analysis
description: 解析和结构化提取简历信息的专业技能
tools: [analyze_resume]
trigger: 当需要解析候选人简历时激活
---

# 简历解析技能

## 执行步骤
1. 接收原始简历文本
2. 提取：姓名、邮箱、技能列表、工作年限、学历、摘要
3. 输出结构化 CandidateInfo JSON

## 质量检查
- 确保姓名非空
- 验证邮箱格式
- 技能列表至少包含 1 项
