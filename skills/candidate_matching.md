---

## name: candidate_matching
description: 评估候选人与岗位需求的匹配程度并生成评分
tools: [score_match, search_candidates]
trigger: 当需要评估候选人与JD匹配度或搜索候选人时激活

# 候选人匹配评分技能

## 执行步骤

1. 解析岗位需求（JD），提取必须技能、加分技能、年限要求
2. 调用 search_candidates 检索语义相似的候选人
3. 对每位候选人调用 score_match 进行逐项对比评分
4. 按匹配分数降序排列，输出结构化 MatchResult 列表

## 质量检查

- 匹配分数范围 0-100
- matched_skills 和 missing_skills 不重叠
- 高分候选人（>=70）标记 should_proceed=True
- 每位候选人都有 recommendation 文本