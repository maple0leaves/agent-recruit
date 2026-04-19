---
name: report_generation
description: 汇总候选人评估结果并生成结构化招聘推荐报告
tools: [query_candidate_history, send_interview_invite, send_rejection_email]
trigger: 当需要生成最终招聘报告或发送通知时激活
---

# 报告生成技能

## 执行步骤
1. 收集所有候选人的 MatchResult 评分数据
2. 查询候选人历史记录（query_candidate_history）补充上下文
3. 按匹配分数排序，生成包含排名、优劣势、建议的推荐报告
4. 对推荐候选人发送面试邀请（send_interview_invite）
5. 对不推荐候选人发送婉拒邮件（send_rejection_email）

## 质量检查
- 报告包含候选人排名、优势、不足、面试建议、总体建议
- 语言简洁专业，方便 HR 快速决策
- 推荐与不推荐的理由与 MatchResult 数据一致
