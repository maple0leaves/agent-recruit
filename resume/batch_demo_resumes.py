#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批量生成虚构技术简历 .tex（用于招聘系统测试），勿用于真实求职。"""

from __future__ import annotations

from pathlib import Path


def esc(s: str) -> str:
    """LaTeX 转义（正文片段）。"""
    s = s.replace("\\", "\\textbackslash{}")
    s = s.replace("&", "\\&")
    s = s.replace("%", "\\%")
    s = s.replace("#", "\\#")
    s = s.replace("_", "\\_")
    s = s.replace("{", "\\{")
    s = s.replace("}", "\\}")
    s = s.replace("~", "\\textasciitilde{}")
    s = s.replace("^", "\\^{}")
    return s


PREAMBLE = r"""%% !TeX TS-program = xelatex
%% 虚构演示简历 — 仅用于 hellojobs 测试数据
\documentclass{resume-photo}
\usepackage{xeCJK}
\setCJKmainfont{Noto Serif CJK SC}
\usepackage{fontspec}
\usepackage{enumitem}
\setlist[itemize]{itemsep=0pt, topsep=1pt, parsep=0pt, partopsep=0pt}

\ResumeName{%(name)s}

\begin{document}

\ResumeContacts{
  %(phone)s,%%
  \ResumeUrl{mailto:%(email)s}{%(email)s},%%
  \textnormal{%(school_line)s}%%
}

\ResumeTitle

\noindent %(summary)s

\section{教育背景}
%(education)s
%(education_extra)s

\section{专业技能}
\begin{itemize}
%(skills)s
\end{itemize}

\section{实习经历}
%(internship)s
%(internship2)s

\section{项目经历}
%(projects)s
%(projects2)s

\section{个人荣誉}
\begin{itemize}
%(honors)s
\end{itemize}

\end{document}
"""


def itemize_lines(items: list[str]) -> str:
    """item 行已按 LaTeX 写好（可含 \\textbf 等），不做 esc。"""
    return "\n".join(f"  \\item {x}" for x in items)


def resume_item(title: str, subtitle: str, date: str, body: list[str]) -> str:
    sub = f"[\\textnormal{{{esc(subtitle)}}}]" if subtitle else "[]"
    dt = f"[{esc(date)}]" if date else "[]"
    return (
        f"\\ResumeItem\n{{{esc(title)}}}\n{sub}\n{dt}\n\n"
        f"\\begin{{itemize}}\n{itemize_lines(body)}\n\\end{{itemize}}\n\n"
    )


# ---------- 增厚：保证每份约 0.8 页以上（虚构内容）----------
SUMMARY_SUPPLEMENT = (
    "注重可观测性与文档沉淀，习惯在评审阶段拆解风险；"
    "参与线上复盘与跨团队联调，英语 CET-6，可阅读官方文档与 RFC（演示数据）。"
)

SKILL_TAIL_LINES = [
    "熟悉 Linux 日常运维与 Shell，具备日志检索与 CPU/内存突增初步定位能力。",
    "掌握 Git / CI 与 Code Review，了解 Docker 与 Kubernetes 基本编排与滚动发布。",
    "了解 OAuth2 / JWT、接口幂等与 REST 规范，具备单元测试与集成测试习惯（JUnit/pytest 等）。",
    "能阅读英文技术文档，具备跨团队沟通与需求澄清能力（测试简历）。",
]

HONOR_TAIL_LINES = [
    "全国计算机等级考试四级（网络工程师）（演示）",
    "校级「优秀学生干部 / 优秀团员」或技术社团骨干（综合测评前 15\\%）",
    "开源贡献：向知名项目提交被合并的 PR（文档/测试/feature）（演示）",
]

EDU_EXTRA_POOL = [
    resume_item(
        "学术交流与在线课程",
        "暑校 / MOOC / 厂商认证（演示）",
        "2022—2025",
        [
            "完成《深入理解计算机系统》配套实验与 MIT 6.828 / 6.S081 公开课部分章节跟做。",
            "Coursera / edX 分布式系统、云计算相关专项课程结业证书 4 门（虚构编号）。",
            "通过 AWS SAA / 阿里云 ACP / Redis 开发者等认证中的 1--2 项（简历测试数据）。",
            "参加 CCF CCSP / 华为 ICT / 百度之星等学科竞赛集训营并完成全部作业。",
        ],
    ),
    resume_item(
        "科研训练与竞赛",
        "大创 / 挑战杯 / 互联网+（演示）",
        "2021—2025",
        [
            "主持或核心参与校级大创项目 1 项，负责方案设计、里程碑管理与中期答辩材料。",
            "挑战杯 / 互联网+ 校赛金奖团队成员，负责技术方案书与 Demo 部署脚本。",
            "在实验室周会中汇报进展 10+ 次，形成实验记录与可复现实验脚本仓库。",
            "协助导师撰写专利交底书 1 份（流程中，测试数据）。",
        ],
    ),
    resume_item(
        "国际交流（演示）",
        "暑期学校 / 线上联合项目",
        "2023—2024",
        [
            "参加海外高校暑期学校（在线），完成 Distributed Systems 课程 Project 3 个。",
            "与海外小组合作完成跨时区项目，使用 Slack/Discord 进行异步协作与代码评审。",
            "撰写全英文技术报告 8 页，获得课程组 Best Presentation 提名（测试数据）。",
            "口语与写作训练：技术博客英文化 5 篇，累计阅读量 1.2 万（演示）。",
        ],
    ),
    resume_item(
        "实验室与助教",
        "本科生科研 / 课程助教",
        "2022—2025",
        [
            "进入校级重点实验室参与课题，负责数据采集、清洗与可视化看板搭建。",
            "担任《数据结构》《操作系统》课程助教，批改作业 200+ 份，答疑课时 40h+。",
            "组织期中复习串讲与上机辅导，课程评教得分位于前 10\\%（演示）。",
            "整理课程 FAQ 与实验踩坑文档，被后续年级沿用。",
        ],
    ),
    resume_item(
        "企业开放日与实训",
        "短期实训营（演示）",
        "2023—2024",
        [
            "参加头部互联网公司 2 周封闭实训，完成从需求到上线的完整小组项目。",
            "在实训中负责接口设计与联调，小组答辩成绩排名前 20\\%。",
            "获得实训营「优秀学员」与内推绿色通道（测试数据，勿当真）。",
            "沉淀实训笔记 1.5 万字，含架构图与排错记录。",
        ],
    ),
]

def _int2_pool() -> list[str]:
    return [
        resume_item(
            "美团 | 到店技术部",
            "后端开发日常实习",
            "2023.07—2024.01",
            [
                "\\textbf{背景}: 营销活动报名接口在晚高峰出现线程池打满与超时尖刺。",
                "\\textbf{方案}: 引入异步化改造与 Sentinel 限流，拆分热点读请求至本地缓存。",
                "\\textbf{指标}: 接口 P99 从 890ms 降至 260ms，错误率从 0.8\\% 降至 0.05\\%。",
                "\\textbf{工程}: 补齐监控大盘与告警分级，编写上线 checklist 与回滚脚本。",
                "\\textbf{协作}: 与前端、测试对齐幂等键与重试策略，完成灰度 5\\%→100\\%。",
            ],
        ),
        resume_item(
            "滴滴出行 | 平台技术",
            "Java 研发实习生",
            "2023.06—2023.12",
            [
                "\\textbf{职责}: 参与订单状态机与补偿任务调度模块维护，处理边界状态脏数据。",
                "\\textbf{优化}: 将部分同步 RPC 改为消息驱动，削峰填谷，峰值下游 QPS 下降 35\\%。",
                "\\textbf{质量}: 推动关键路径单测覆盖率从 52\\% 提升到 71\\%，引入契约测试。",
                "\\textbf{排障}: 通过链路追踪定位跨城调用 RT 抖动，优化连接池与超时配置。",
                "\\textbf{文档}: 输出故障演练手册与 Runbook，被组内采纳为 on-call 参考。",
            ],
        ),
        resume_item(
            "中国工商银行 | 软件开发中心",
            "金科研发实习生",
            "2024.01—2024.06",
            [
                "\\textbf{合规}: 在监管要求下完成日志脱敏与字段分级打标方案落地。",
                "\\textbf{批处理}: 参与日终对账任务优化，将窗口期从 4.5h 压缩到 3.1h。",
                "\\textbf{数据库}: 协助 DBA 分析慢 SQL，增加覆盖索引与分页改写，平均耗时下降 62\\%。",
                "\\textbf{安全}: 参与渗透测试整改，修复 XSS 与越权访问类问题 6 处。",
                "\\textbf{流程}: 熟悉银行版本发布、双人复核与变更窗口制度。",
            ],
        ),
        resume_item(
            "小米集团 | 互联网商业部",
            "广告服务端实习生",
            "2023.12—2024.05",
            [
                "\\textbf{业务}: 参与广告召回与排序链路监控埋点，建设异常流量识别规则。",
                "\\textbf{性能}: 优化 protobuf 序列化热点，CPU 占用下降约 8\\%。",
                "\\textbf{数据}: 与数据团队协作搭建小时级报表，支持运营策略迭代。",
                "\\textbf{稳定性}: 大促前完成容量评估与限流预案演练 3 轮。",
                "\\textbf{总结}: 输出「大促保障清单」模板并在组内复用。",
            ],
        ),
        resume_item(
            "SHEIN | 全球技术中心",
            "供应链后端实习生",
            "2024.02—2024.07",
            [
                "\\textbf{场景}: 跨境库存与仓配调度接口高并发读写，存在热点行更新争用。",
                "\\textbf{方案}: 引入分段锁与异步合并写，结合 Binlog 订阅做最终一致。",
                "\\textbf{结果}: 热点 SKU 更新 TPS 上限提升 2.4 倍，锁等待时间下降 70\\%。",
                "\\textbf{工具}: 编写压测脚本与数据构造工具链，纳入 CI nightly。",
                "\\textbf{协作}: 与仓储 WMS 团队对齐字段口径，消除跨系统对账差异。",
            ],
        ),
        resume_item(
            "贝壳找房 | 如视",
            "C++/Go 工程实习生",
            "2023.07—2024.01",
            [
                "\\textbf{职责}: 参与三维空间数据处理流水线，负责任务队列与重试策略。",
                "\\textbf{优化}: 调整 gRPC 流式传输参数，大文件传输失败重试率下降 45\\%。",
                "\\textbf{质量}: 引入 fuzz 测试覆盖解析模块，发现边界崩溃 3 类并修复。",
                "\\textbf{部署}: 熟悉 Ansible 批量发布与蓝绿切换流程。",
                "\\textbf{成长}: 完成从业务代码到性能剖析工具链的完整闭环实践。",
            ],
        ),
        resume_item(
            "拼多多 | 交易平台",
            "后端实习生",
            "2024.03—2024.08",
            [
                "\\textbf{活动}: 参与大促「万人团」库存预占与释放逻辑开发与压测。",
                "\\textbf{一致性}: 使用分布式锁 + 版本号控制超卖风险，压测零超卖。",
                "\\textbf{观测}: 搭建 Grafana 看板跟踪关键指标，值班期间 0 P1 事故。",
                "\\textbf{复盘}: 参与事故复盘 2 次，输出改进项并跟踪闭环。",
                "\\textbf{代码}: MR 平均评论轮次 4 轮，注重可读性与边界条件注释。",
            ],
        ),
        resume_item(
            "百度 | 移动生态",
            "后端研发实习生",
            "2023.06—2023.11",
            [
                "\\textbf{检索}: 参与搜索相关性特征工程与离线任务调度稳定性治理。",
                "\\textbf{存储}: 优化 HBase Get 批量模式，P95 延迟下降 19\\%。",
                "\\textbf{平台}: 熟悉内部 BVC 构建与发布流水线。",
                "\\textbf{算法对接}: 与算法同学联调 A/B 实验埋点与分流一致性校验。",
                "\\textbf{文档}: 维护接口字典与错误码说明，降低联调沟通成本。",
            ],
        ),
        resume_item(
            "科大讯飞 | 教育 BG",
            "Java 实习生",
            "2024.01—2024.06",
            [
                "\\textbf{业务}: 参与智慧课堂题库与阅卷统计服务接口开发。",
                "\\textbf{安全}: 完成接口鉴权加固与敏感字段脱敏改造。",
                "\\textbf{性能}: MyBatis 二级缓存策略评估后改为本地 Caffeine + 广播失效。",
                "\\textbf{测试}: 引入 Testcontainers 做 MySQL 集成测试，回归用例 +120 条。",
                "\\textbf{交付}: 按期完成 3 个迭代，需求变更率控制在 15\\% 以内。",
            ],
        ),
        resume_item(
            "海康威视 | 行业应用",
            "嵌入式 / 后端实习生",
            "2023.09—2024.02",
            [
                "\\textbf{设备接入}: 参与国标设备接入网关协议适配与异常码映射。",
                "\\textbf{可靠性}: 实现断线重连与心跳退避策略，掉线恢复时间缩短 40\\%。",
                "\\textbf{日志}: 统一日志格式与 traceId 透传，问题定位时间减半。",
                "\\textbf{客户}: 支持 2 次驻场联调，收集需求并转化为可验收用例。",
                "\\textbf{规范}: 熟悉编码规范与静态检查门禁，CI 全绿方可合并。",
            ],
        ),
        resume_item(
            "网易 | 杭州研究院",
            "中间件方向实习生",
            "2023.07—2024.01",
            [
                "\\textbf{消息}: 参与 MQ 控制台 Topic 治理与消息轨迹查询性能优化。",
                "\\textbf{存储}: 调研并输出对象存储冷热分层方案对比报告 25 页。",
                "\\textbf{演练}: 参与双活切换演练，验证 RPO/RTO 指标达标。",
                "\\textbf{开源}: 向社区组件提交文档 PR 2 个并被合并。",
                "\\textbf{软技能}: 跨 3 团队协调排期，保证里程碑按时交付。",
            ],
        ),
    ]


def _pr2_pool() -> list[str]:
    return [
        resume_item(
            "统一配置中心改造",
            "Spring Cloud Config → Nacos（演示）",
            "2024.01—2024.04",
            [
                "\\textbf{目标}: 解决配置分散、无灰度与无审计问题，支撑 80+ 微服务。",
                "\\textbf{方案}: 双写双读迁移，配置变更走审批流与版本快照。",
                "\\textbf{结果}: 配置发布平均耗时从 25min 降至 3min，人为误配下降 60\\%。",
                "\\textbf{风险}: 设计回滚开关与只读兜底文件，演练 2 次成功。",
            ],
        ),
        resume_item(
            "日志检索与告警平台",
            "ELK + 规则引擎（演示）",
            "2023.10—2024.03",
            [
                "\\textbf{痛点}: 多业务线日志格式不统一，检索慢且告警噪声高。",
                "\\textbf{落地}: 制定 log schema，Filebeat 多管道 + Ingest Pipeline 清洗。",
                "\\textbf{指标}: 检索 P95 从 4.2s 降至 0.9s，告警误报率下降 55\\%。",
                "\\textbf{运营}: 建立 on-call 轮值与告警分级 SOP。",
            ],
        ),
        resume_item(
            "灰度发布与流量染色",
            "网关 + 标签路由（演示）",
            "2024.02—2024.06",
            [
                "\\textbf{能力}: 基于用户 ID / 地域 / 白名单实现多维度灰度与染色。",
                "\\textbf{实现}: 扩展网关插件，透传染色 Header 至下游 RPC Metadata。",
                "\\textbf{验证}: 与 QA 共建自动化回归集，覆盖 200+ 核心用例。",
                "\\textbf{效果}: 月均生产配置事故从 3 起降至 0.5 起（演示数据）。",
            ],
        ),
        resume_item(
            "多租户 SaaS 计费引擎",
            "订阅制 + 用量计费（演示）",
            "2023.09—2024.02",
            [
                "\\textbf{模型}: 设计套餐、用量累计、账单周期与 proration 规则。",
                "\\textbf{一致}: 使用 Outbox + 消息表保证计费事件与财务对账一致。",
                "\\textbf{性能}: 批价任务分片并行，账单生成时间缩短 48\\%。",
                "\\textbf{测试}: 构造边界用例库 150+，覆盖闰月与升级降级场景。",
            ],
        ),
        resume_item(
            "实时风控规则引擎",
            "Drools / 自研 DSL（演示）",
            "2024.01—2024.05",
            [
                "\\textbf{需求}: 支持运营侧快速上线规则，T+0 生效且可审计。",
                "\\textbf{架构}: 规则编译为字节码缓存，热加载版本号隔离。",
                "\\textbf{指标}: 规则平均评估耗时 <2ms，峰值 QPS 12k 稳定。",
                "\\textbf{治理}: 规则变更双人复核 + 影子流量对比。",
            ],
        ),
        resume_item(
            "低代码表单引擎",
            "拖拽 + JSON Schema（演示）",
            "2023.07—2023.12",
            [
                "\\textbf{前端}: 基于 React 实现组件注册表与撤销重做栈。",
                "\\textbf{后端}: 动态表单元数据存储与版本迁移脚本。",
                "\\textbf{生态}: 导出 JSON 与后端校验规则一致，减少联调返工。",
                "\\textbf{采用}: 在内 3 个业务线试点，表单搭建时间缩短 70\\%（演示）。",
            ],
        ),
        resume_item(
            "IoT 设备 OTA 平台",
            "差分包 + 回滚（演示）",
            "2024.02—2024.07",
            [
                "\\textbf{安全}: 固件签名校验与分块哈希校验，防篡改。",
                "\\textbf{体验}: 断点续传与静默升级策略可配置，失败自动回滚。",
                "\\textbf{规模}: 管理设备 10 万台级模拟压测通过（测试数据）。",
                "\\textbf{观测}: OTA 成功率、重试次数与版本分布实时大盘。",
            ],
        ),
        resume_item(
            "数据血缘与元数据管理",
            "Atlas 类方案（演示）",
            "2023.10—2024.04",
            [
                "\\textbf{采集}: SQL 解析 + 日志埋点双通道，覆盖 Hive/Spark/Flink 任务。",
                "\\textbf{价值}: 影响分析时间从数小时缩短到分钟级。",
                "\\textbf{治理}: 推动核心表负责人认领与分级打标。",
                "\\textbf{交付}: 提供开放 API 供数据质量平台订阅血缘变更。",
            ],
        ),
        resume_item(
            "API 网关插件体系",
            "鉴权 / 限流 / 审计（演示）",
            "2024.01—2024.06",
            [
                "\\textbf{扩展}: 定义插件 SPI，支持 Lua / WASM 沙箱（演示）。",
                "\\textbf{安全}: 统一 JWT 校验与 mTLS 可选链路。",
                "\\textbf{运维}: 插件热更新与版本回滚，0 停机。",
                "\\textbf{指标}: 网关自身 CPU 开销 <3\\% 额外基线（压测）。",
            ],
        ),
        resume_item(
            "特征存储与在线推理",
            "Feast 类实践（演示）",
            "2023.08—2024.01",
            [
                "\\textbf{一致}: 离线在线特征对齐，监控 PSI 漂移。",
                "\\textbf{延迟}: 在线特征查询 P99 <6ms，支撑排序模型实时更新。",
                "\\textbf{平台}: 与模型服务 gRPC 联调，完成金丝雀发布。",
                "\\textbf{文档}: 输出特征字典与血缘说明，供算法与工程共用。",
            ],
        ),
    ]


INT2_POOL = _int2_pool()
PR2_POOL = _pr2_pool()


def _extras_for(stem: str) -> dict[str, str]:
    """按文件名哈希轮换模板，避免 30 份完全雷同。"""
    h = hash(stem)
    edu = EDU_EXTRA_POOL[h % len(EDU_EXTRA_POOL)]
    i2 = INT2_POOL[(h * 17) % len(INT2_POOL)]
    p2 = PR2_POOL[(h * 31) % len(PR2_POOL)]
    return {
        "education_extra": edu,
        "internship2": i2,
        "projects2": p2,
    }


# 30 份：姓名、文件名、学校行、邮箱域、电话、简介、教育、技能、实习、项目、荣誉
PROFILES: list[dict] = [
    {
        "file": "zhang_wei",
        "name": "张伟",
        "school_line": "浙江大学 | 软件工程 · 硕士 | 2023—2026",
        "email": "zhangwei26@zju.edu.cn",
        "phone": "138-0001-0001",
        "summary": "主攻 Java 与分布式微服务，熟悉 Spring Cloud、Kafka 与 MySQL 分库分表；在电商高并发场景完成接口 P99 从 420ms 降至 180ms 的优化实践。",
        "education": resume_item(
            "浙江大学",
            "软件学院 | 软件工程 | 硕士 | 排名前 10%",
            "2023.09—2026.06(预计)",
            ["核心课程：分布式系统、中间件原理、高可用架构设计。"],
        )
        + resume_item(
            "浙江大学",
            "计算机学院 | 软件工程 | 学士",
            "2019.09—2023.06",
            ["校级优秀毕业生，ACM 校赛银牌。"],
        ),
        "skills": itemize_lines(
            [
                "熟悉 Java、JVM 调优与 Spring Boot / Spring Cloud Alibaba 微服务栈。",
                "掌握 MySQL 索引与事务、Redis 缓存与分布式锁、RocketMQ 异步解耦。",
                "了解 Kubernetes 部署与 SkyWalking 链路追踪，具备线上问题定位经验。",
            ]
        ),
        "internship": resume_item(
            "阿里巴巴集团 | 本地生活",
            "Java 开发实习生",
            "2024.07—2025.01",
            [
                "\\textbf{职责}: 参与营销中台订单接口改造，日均调用量约 2 亿次。",
                "\\textbf{成果}: 通过批量查询与本地缓存，核心下单链路 P99 延迟下降 58\\%。",
            ],
        ),
        "projects": resume_item(
            "秒杀系统课程设计",
            "高并发库存与限流",
            "2024.03—2024.06",
            [
                "基于 Redis 预减库存 + Lua 脚本保证原子性，支撑压测峰值 1.2 万 QPS。",
                "网关层令牌桶限流，误杀率控制在 0.3\\% 以下。",
            ],
        ),
        "honors": itemize_lines(
            [
                "中国高校计算机大赛 网络技术挑战赛 华东赛区 一等奖",
                "浙江大学 学业优秀奖学金 二等",
            ]
        ),
    },
    {
        "file": "li_ming",
        "name": "李明",
        "school_line": "上海交通大学 | 计算机科学与技术 · 硕士 | 2022—2025",
        "email": "liming@sjtu.edu.cn",
        "phone": "138-0002-0002",
        "summary": "Go 语言与云原生方向，熟悉 gRPC、etcd 与 Operator 开发；参与内部 PaaS 控制面组件交付，单元测试覆盖率提升至 78%。",
        "education": resume_item(
            "上海交通大学",
            "电子信息与电气工程学院 | 计算机科学与技术 | 硕士",
            "2022.09—2025.06",
            ["研究方向：容器调度与多集群联邦。"],
        ),
        "skills": itemize_lines(
            [
                "掌握 Go、Kubernetes、Prometheus/Grafana 监控体系。",
                "熟悉 Docker 镜像分层优化与 CI/CD（GitLab CI、Argo CD）。",
                "了解 Istio 流量管理与 gRPC 服务网格实践。",
            ]
        ),
        "internship": resume_item(
            "字节跳动 | 基础架构",
            "云原生开发实习生",
            "2024.06—2024.12",
            [
                "\\textbf{职责}: 维护多集群节点生命周期 Operator，对接公司 CMDB。",
                "\\textbf{成果}: 节点就绪平均时间从 4.2min 降至 1.1min，线上故障工单下降 35\\%。",
            ],
        ),
        "projects": resume_item(
            "轻量级 K8s 审计日志聚合",
            "Fluent Bit + Kafka",
            "2024.01—2024.05",
            [
                "设计 Sidecar 采集策略，日日志量约 800GB 场景下 ES 写入失败率 <0.02\\%。",
            ],
        ),
        "honors": itemize_lines(["上海交通大学 优秀研究生干部", "开源之夏 OSPP 结项（Kubernetes 相关）"]),
    },
    {
        "file": "wang_fang",
        "name": "王芳",
        "school_line": "复旦大学 | 软件工程 · 学士 | 2021—2025",
        "email": "wangfang@fudan.edu.cn",
        "phone": "138-0003-0003",
        "summary": "前端工程化与可视化，熟练使用 React、TypeScript 与 Vite；主导管理后台从 Webpack 迁移至 Vite，冷启动时间缩短约 70%。",
        "education": resume_item(
            "复旦大学",
            "软件学院 | 软件工程 | 学士",
            "2021.09—2025.06",
            ["前端方向：性能优化与组件库建设。"],
        ),
        "skills": itemize_lines(
            [
                "熟悉 React 18、Hooks、Zustand 与 React Query 数据层。",
                "掌握 TypeScript 严格模式、ECharts/Ant Design Pro 中后台实践。",
                "了解 Node.js BFF 与 Nginx 部署，具备 Lighthouse 性能调优经验。",
            ]
        ),
        "internship": resume_item(
            "美团 | 到店事业群",
            "前端开发实习生",
            "2024.07—2025.01",
            [
                "\\textbf{职责}: 营销活动搭建平台低代码表单引擎维护。",
                "\\textbf{成果}: 表单渲染首屏 FCP 从 2.1s 降至 0.9s（4G 弱网模拟）。",
            ],
        ),
        "projects": resume_item(
            "Monorepo 组件库",
            "pnpm + Turborepo",
            "2023.10—2024.04",
            [
                "抽取 40+ 业务组件，Storybook 文档覆盖率 100\\%，跨 3 个业务线复用。",
            ],
        ),
        "honors": itemize_lines(["复旦大学 优秀学生奖学金", "全国大学生计算机设计大赛 二等奖"]),
    },
    {
        "file": "liu_yang",
        "name": "刘洋",
        "school_line": "中国科学技术大学 | 计算机应用技术 · 硕士 | 2023—2026",
        "email": "liuyang@mail.ustc.edu.cn",
        "phone": "138-0004-0004",
        "summary": "计算机视觉与多模态，熟悉 PyTorch、DETR 系列与模型蒸馏；在工业缺陷检测数据集上 mAP@0.5 提升 6.2 个百分点。",
        "education": resume_item(
            "中国科学技术大学",
            "计算机学院 | 计算机应用技术 | 硕士",
            "2023.09—2026.06(预计)",
            ["实验室：媒体计算与智能感知。"],
        ),
        "skills": itemize_lines(
            [
                "掌握 Python、PyTorch，熟悉目标检测、实例分割与半监督学习。",
                "了解 TensorRT 推理加速与 ONNX 导出流程。",
                "熟悉 OpenCV、Albumentations 数据增强管线。",
            ]
        ),
        "internship": resume_item(
            "商汤科技",
            "计算机视觉算法实习生",
            "2024.06—2024.12",
            [
                "\\textbf{职责}: 产线 AOI 小样本缺陷检测模型迭代。",
                "\\textbf{成果}: 在 500 张标注数据上 Recall@90\\%Precision 提升 11\\%。",
            ],
        ),
        "projects": resume_item(
            "轻量化检测头设计",
            "毕业设计课题",
            "2024.03—至今",
            [
                "引入可分离卷积与特征金字塔重加权，参数量下降 40\\%，速度提升 22 FPS。",
            ],
        ),
        "honors": itemize_lines(["VALSE 2024 学生志愿者", "中科大 学业奖学金 一等"]),
    },
    {
        "file": "chen_jing",
        "name": "陈静",
        "school_line": "北京大学 | 智能科学与技术 · 硕士 | 2022—2025",
        "email": "chenjing@pku.edu.cn",
        "phone": "138-0005-0005",
        "summary": "大模型应用与 RAG，熟悉 LangChain、向量检索与 LoRA 微调；构建企业内部知识问答，Top-5 命中率离线评测达 81%。",
        "education": resume_item(
            "北京大学",
            "智能学院 | 智能科学与技术 | 硕士",
            "2022.09—2025.06",
            ["导师方向：自然语言处理与知识增强生成。"],
        ),
        "skills": itemize_lines(
            [
                "熟悉 Transformers、PEFT、FAISS/Milvus 向量检索。",
                "掌握 Prompt 工程、RAG 流水线与评测集构建。",
                "了解 vLLM 推理服务化与 GPU 显存优化。",
            ]
        ),
        "internship": resume_item(
            "智谱 AI",
            "大模型应用研发实习生",
            "2024.07—2025.01",
            [
                "\\textbf{职责}: 企业客服 Copilot 工具链与评测看板。",
                "\\textbf{成果}: 人工抽检一致率从 72\\% 提升至 84\\%。",
            ],
        ),
        "projects": resume_item(
            "多跳问答 RAG",
            "课程项目",
            "2024.02—2024.06",
            [
                "迭代式检索 + Cross-Encoder 重排，HotpotQA EM 提升 3.8pt。",
            ],
        ),
        "honors": itemize_lines(["ACL 2025 共同作者（在投）", "北京大学 三好学生"]),
    },
    {
        "file": "zhao_lei",
        "name": "赵磊",
        "school_line": "华中科技大学 | 软件工程 · 学士 | 2020—2024",
        "email": "zhaolei@hust.edu.cn",
        "phone": "138-0006-0006",
        "summary": "Android 客户端开发，熟悉 Kotlin、Jetpack Compose 与性能剖析；主导包体积治理，APK 减小 18%。",
        "education": resume_item(
            "华中科技大学",
            "软件学院 | 软件工程 | 学士",
            "2020.09—2024.06",
            ["毕业设计：短视频客户端弱网优化。"],
        ),
        "skills": itemize_lines(
            [
                "熟悉 Kotlin、Android SDK、MVVM 与协程并发。",
                "掌握 LeakCanary、Systrace 与电量/卡顿治理。",
                "了解 JNI 与音视频硬解基础。",
            ]
        ),
        "internship": resume_item(
            "小红书",
            "Android 开发实习生",
            "2023.12—2024.05",
            [
                "\\textbf{职责}: 笔记发布链路稳定性与启动耗时治理。",
                "\\textbf{成果}: 冷启动主线程耗时降低 120ms（P90）。",
            ],
        ),
        "projects": resume_item(
            "Compose 实验性 UI 套件",
            "个人开源",
            "2023.06—2023.12",
            [
                "GitHub 300+ stars，被 2 个示例项目引用。",
            ],
        ),
        "honors": itemize_lines(["蓝桥杯软件类 全国一等奖", "华中科技大学 自强奖学金"]),
    },
    {
        "file": "sun_yue",
        "name": "孙悦",
        "school_line": "北京航空航天大学 | 软件工程 · 硕士 | 2023—2026",
        "email": "sunyue@buaa.edu.cn",
        "phone": "138-0007-0007",
        "summary": "iOS 与 SwiftUI，熟悉 Combine、Core Data 与网络层封装；实习期间负责金融 App 安全键盘与证书钉扎改造。",
        "education": resume_item(
            "北京航空航天大学",
            "软件学院 | 软件工程 | 硕士",
            "2023.09—2026.06(预计)",
            ["移动与嵌入式软件方向。"],
        ),
        "skills": itemize_lines(
            [
                "掌握 Swift、UIKit/SwiftUI、Xcode Instruments。",
                "熟悉 HTTPS 证书钉扎、Keychain 与防截屏策略。",
                "了解 Objective-C 互操作与 SPM 模块化。",
            ]
        ),
        "internship": resume_item(
            "东方财富",
            "iOS 开发实习生",
            "2024.07—2024.12",
            [
                "\\textbf{职责}: 交易模块崩溃率治理与启动框架拆分。",
                "\\textbf{成果}: 崩溃率从 0.35\\% 降至 0.12\\%（周活维度）。",
            ],
        ),
        "projects": resume_item(
            "SwiftUI 股票分时图组件",
            "课程设计",
            "2024.03—2024.06",
            [
                "Canvas 绘制 + 手势缩放，帧率稳定在 55+ FPS（iPhone 12）。",
            ],
        ),
        "honors": itemize_lines(["中国大学生服务外包创新创业大赛 国家三等奖", "北航 学习优秀奖学金"]),
    },
    {
        "file": "wu_hao",
        "name": "吴昊",
        "school_line": "电子科技大学 | 计算机科学与技术 · 学士 | 2021—2025",
        "email": "wuhao@uestc.edu.cn",
        "phone": "138-0008-0008",
        "summary": "游戏客户端与图形，熟悉 C++17、Unreal 蓝图与性能分析；参与手游战斗同步与延迟补偿模块开发。",
        "education": resume_item(
            "电子科技大学",
            "计算机科学与工程学院 | 计算机科学与技术 | 学士",
            "2021.09—2025.06",
            ["图形学、游戏引擎选修为主。"],
        ),
        "skills": itemize_lines(
            [
                "熟悉 C++、Unreal Engine 5、内存与渲染性能剖析。",
                "了解 UDP 状态同步、插值与客户端预测。",
                "掌握 Git Perforce 协作与 CrashSight 符号化。",
            ]
        ),
        "internship": resume_item(
            "某头部手游工作室",
            "客户端开发实习生",
            "2024.06—2024.12",
            [
                "\\textbf{职责}: PVP 技能表现与网络同步问题排查。",
                "\\textbf{成果}: 高延迟场景下技能判定投诉量下降约 40\\%。",
            ],
        ),
        "projects": resume_item(
            "Mini 物理引擎实验",
            "UE5 + C++",
            "2023.10—2024.04",
            [
                "实现简化刚体碰撞与固定步长积分，用于教学 Demo。",
            ],
        ),
        "honors": itemize_lines(["腾讯游戏高校创意制作大赛 赛区优秀奖", "电子科大 优秀共青团员"]),
    },
    {
        "file": "xu_lin",
        "name": "徐琳",
        "school_line": "西安电子科技大学 | 物联网工程 · 硕士 | 2022—2025",
        "email": "xulin@stu.xidian.edu.cn",
        "phone": "138-0009-0009",
        "summary": "嵌入式 Linux 与 RTOS，熟悉 FreeRTOS、STM32 与驱动开发；完成工业网关 Modbus 转 MQTT 量产固件维护。",
        "education": resume_item(
            "西安电子科技大学",
            "通信工程学院 | 物联网工程 | 硕士",
            "2022.09—2025.06",
            ["嵌入式系统与边缘计算实验室。"],
        ),
        "skills": itemize_lines(
            [
                "熟悉 C、FreeRTOS、UART/SPI/I2C 与常见传感器驱动。",
                "掌握 Wireshark 抓包、gdb 远程调试与 OTA 差分升级。",
                "了解 MQTT、CoAP 与 TLS 在资源受限设备上的裁剪。",
            ]
        ),
        "internship": resume_item(
            "华为西安研究所",
            "嵌入式软件实习生",
            "2024.07—2024.12",
            [
                "\\textbf{职责}: IoT 模组功耗与唤醒时序优化。",
                "\\textbf{成果}: 深度睡眠电流下降 22\\%，满足客户标书指标。",
            ],
        ),
        "projects": resume_item(
            "边缘网关协议栈",
            "校企课题",
            "2024.01—2024.08",
            [
                "支持 200+ 子设备并发轮询，CPU 占用峰值 <35\\%（Cortex-A7）。",
            ],
        ),
        "honors": itemize_lines(["全国大学生嵌入式芯片设计大赛 华东二等奖", "西电 研究生学业奖学金"]),
    },
    {
        "file": "zhou_qiang",
        "name": "周强",
        "school_line": "武汉大学 | 信息安全 · 学士 | 2020—2024",
        "email": "zhouqiang@whu.edu.cn",
        "phone": "138-0010-0010",
        "summary": "Web 安全与渗透测试，熟悉 OWASP Top 10、Burp Suite 与 Python 自动化扫描；为校内 SRC 提交有效漏洞 12 个。",
        "education": resume_item(
            "武汉大学",
            "国家网络安全学院 | 信息安全 | 学士",
            "2020.09—2024.06",
            ["CTF 战队成员，主攻 Web 与 Crypto。"],
        ),
        "skills": itemize_lines(
            [
                "熟悉 HTTP/S 协议、JWT 安全、SSRF/反序列化常见利用与修复。",
                "掌握 Python 脚本化扫描与 Frida 动态分析入门。",
                "了解 SDL 安全开发生命周期与依赖漏洞治理（SCA）。",
            ]
        ),
        "internship": resume_item(
            "奇安信",
            "安全研究实习生",
            "2024.03—2024.08",
            [
                "\\textbf{职责}: 政企客户 Web 资产漏洞验证与报告撰写。",
                "\\textbf{成果}: 平均单项目高危漏洞发现数提升 20\\%（同比组内基线）。",
            ],
        ),
        "projects": resume_item(
            "自动化漏洞 PoC 框架",
            "毕业设计",
            "2023.10—2024.05",
            [
                "插件化加载 Nuclei 模板，日均扫描 URL 约 50 万条。",
            ],
        ),
        "honors": itemize_lines(["强网杯 全国总决赛 优胜奖", "武汉大学 优秀学生"]),
    },
    {
        "file": "ma_xin",
        "name": "马欣",
        "school_line": "同济大学 | 计算机科学与技术 · 硕士 | 2023—2026",
        "email": "maxin@tongji.edu.cn",
        "phone": "138-0011-0011",
        "summary": "SRE 与可观测性，熟悉 Prometheus、Thanos 与 OpenTelemetry；推动黄金四指标看板覆盖核心服务 95%。",
        "education": resume_item(
            "同济大学",
            "电子与信息工程学院 | 计算机科学与技术 | 硕士",
            "2023.09—2026.06(预计)",
            ["云计算与智能系统方向。"],
        ),
        "skills": itemize_lines(
            [
                "掌握 Linux、Bash、Python，熟悉 Kubernetes 运维与 HPA/VPA。",
                "熟悉 Prometheus、Grafana、Loki、Alertmanager 告警路由。",
                "了解 Chaos Mesh 故障演练与 SLO 错误预算管理。",
            ]
        ),
        "internship": resume_item(
            "蚂蚁集团",
            "SRE 实习生",
            "2024.06—2024.12",
            [
                "\\textbf{职责}: 支付链路容量评估与大促压测值班。",
                "\\textbf{成果}: 压测脚本复用率提升，准备时间缩短 45\\%。",
            ],
        ),
        "projects": resume_item(
            "统一 TraceID 注入中间件",
            "实验室项目",
            "2024.02—2024.07",
            [
                "基于 OTel Java Agent 扩展，跨 30+ 微服务调用链完整率 98.6\\%。",
            ],
        ),
        "honors": itemize_lines(["同济大学 优秀学生奖学金", "云原生技术沙龙 优秀分享者"]),
    },
    {
        "file": "huang_ting",
        "name": "黄婷",
        "school_line": "中山大学 | 数据科学与大数据技术 · 学士 | 2021—2025",
        "email": "huangting@mail.sysu.edu.cn",
        "phone": "138-0012-0012",
        "summary": "数据工程与离线数仓，熟悉 Hive、Spark SQL 与数据质量规则；参与日增量 10TB 级日志入仓分层建模。",
        "education": resume_item(
            "中山大学",
            "计算机学院 | 数据科学与大数据技术 | 学士",
            "2021.09—2025.06",
            ["大数据平台与可视化选修。"],
        ),
        "skills": itemize_lines(
            [
                "熟悉 SQL、Hive、Spark、Airflow 调度与分区治理。",
                "掌握数据质量（Great Expectations 思想）与血缘文档化。",
                "了解 ClickHouse 与 OLAP 查询优化入门。",
            ]
        ),
        "internship": resume_item(
            "网易",
            "数据开发实习生",
            "2024.07—2024.12",
            [
                "\\textbf{职责}: 游戏埋点 DWD 表重构与缓慢变化维处理。",
                "\\textbf{成果}: 下游任务平均运行时长下降 28\\%。",
            ],
        ),
        "projects": resume_item(
            "用户留存漏斗实时看板",
            "大作业",
            "2024.03—2024.06",
            [
                "Flink SQL + Redis 维表，端到端延迟 P99 <8s。",
            ],
        ),
        "honors": itemize_lines(["全国大学生数学建模竞赛 省一等奖", "中山大学 优秀志愿者"]),
    },
    {
        "file": "lin_jie",
        "name": "林杰",
        "school_line": "东南大学 | 软件工程 · 硕士 | 2022—2025",
        "email": "linjie@seu.edu.cn",
        "phone": "138-0013-0013",
        "summary": "测试开发与质量保障，熟悉 Pytest、接口自动化与 CI 集成；搭建冒烟套件使主干回归时间从 6h 降至 2h。",
        "education": resume_item(
            "东南大学",
            "计算机科学与工程学院 | 软件工程 | 硕士",
            "2022.09—2025.06",
            ["软件测试与可靠性方向。"],
        ),
        "skills": itemize_lines(
            [
                "熟悉 Python、Pytest、Requests、Allure 报告与 Jenkins Pipeline。",
                "掌握 Postman/Newman、Mock Server 与契约测试入门。",
                "了解 Docker 化测试环境与覆盖率门禁（JaCoCo）。",
            ]
        ),
        "internship": resume_item(
            "携程",
            "测试开发实习生",
            "2024.06—2024.12",
            [
                "\\textbf{职责}: 酒店库存接口自动化与流量回放验证。",
                "\\textbf{成果}: 线上 P1 缺陷漏测率季度环比下降 40\\%。",
            ],
        ),
        "projects": resume_item(
            "基于标签的用例选择器",
            "课题 Demo",
            "2024.01—2024.05",
            [
                "结合代码变更 Diff 与用例标签，平均执行用例数减少 62\\%。",
            ],
        ),
        "honors": itemize_lines(["江苏省互联网+大学生创新创业大赛 铜奖", "东南大学 三好研究生"]),
    },
    {
        "file": "guo_yan",
        "name": "郭岩",
        "school_line": "南京大学 | 计算机科学与技术 · 学士 | 2020—2024",
        "email": "guoyan@nju.edu.cn",
        "phone": "138-0014-0014",
        "summary": "全栈与 Node.js，熟悉 NestJS、TypeORM 与 React；独立交付内部工单系统，日活用户约 800 人。",
        "education": resume_item(
            "南京大学",
            "计算机科学与技术系 | 计算机科学与技术 | 学士",
            "2020.09—2024.06",
            ["Web 全栈与系统设计课程项目丰富。"],
        ),
        "skills": itemize_lines(
            [
                "熟悉 TypeScript、Node.js、NestJS、PostgreSQL、Redis。",
                "掌握 React、Ant Design、Vite 与 REST/GraphQL 基础。",
                "了解 PM2 部署与 Nginx 反向代理、JWT 鉴权。",
            ]
        ),
        "internship": resume_item(
            "SaaS 初创公司",
            "全栈开发实习生",
            "2023.12—2024.06",
            [
                "\\textbf{职责}: 计费模块与多租户数据隔离方案落地。",
                "\\textbf{成果}: 账单对账人工工时从 16h/周 降至 4h/周。",
            ],
        ),
        "projects": resume_item(
            "开源工单插件",
            "GitHub",
            "2023.06—2023.12",
            [
                "npm 周下载量峰值 1.2k，Issue 平均响应时间 <24h。",
            ],
        ),
        "honors": itemize_lines(["南京大学 优秀学生", "开源软件供应链大赛 华东赛区 三等奖"]),
    },
    {
        "file": "he_sen",
        "name": "何森",
        "school_line": "北京理工大学 | 软件工程 · 硕士 | 2023—2026",
        "email": "hesen@bit.edu.cn",
        "phone": "138-0015-0015",
        "summary": "区块链与智能合约，熟悉 Solidity、Hardhat 与 EVM 安全最佳实践；参与联盟链存证模块链码审计辅助。",
        "education": resume_item(
            "北京理工大学",
            "计算机学院 | 软件工程 | 硕士",
            "2023.09—2026.06(预计)",
            ["分布式系统与可信计算交叉方向。"],
        ),
        "skills": itemize_lines(
            [
                "熟悉 Solidity、OpenZeppelin、Hardhat/Foundry 测试。",
                "了解 Hyperledger Fabric 链码生命周期与 CouchDB 状态模型。",
                "掌握常见重入、整数溢出（历史）与访问控制漏洞排查。",
            ]
        ),
        "internship": resume_item(
            "某金融科技公司",
            "区块链研发实习生",
            "2024.07—2024.12",
            [
                "\\textbf{职责}: 存证合约升级与 Gas 优化。",
                "\\textbf{成果}: 单笔存证 Gas 消耗下降约 18\\%。",
            ],
        ),
        "projects": resume_item(
            "NFT 票务 Demo",
            "课程项目",
            "2024.02—2024.06",
            [
                "ERC-721 + 链下元数据 IPFS Pinning，支持二级市场版税 5\\%。",
            ],
        ),
        "honors": itemize_lines(["北京理工大学 学业奖学金", "CCF 区块链专委会 暑期学校 结业"]),
    },
    {
        "file": "yu_tao",
        "name": "于涛",
        "school_line": "哈尔滨工业大学 | 计算机科学与技术 · 硕士 | 2022—2025",
        "email": "yutao@hit.edu.cn",
        "phone": "138-0016-0016",
        "summary": "数据库与存储方向应用研发，熟悉 MySQL 内核参数调优、Binlog 解析与分库分表中间件；支撑订单库峰值 QPS 8k+。",
        "education": resume_item(
            "哈尔滨工业大学",
            "计算学部 | 计算机科学与技术 | 硕士",
            "2022.09—2025.06",
            ["研究方向：分布式事务与一致性。"],
        ),
        "skills": itemize_lines(
            [
                "深入理解 InnoDB、索引、事务隔离级别与锁等待分析。",
                "熟悉 ShardingSphere、Canal 与数据同步延迟监控。",
                "了解 RocksDB 与 LSM-Tree 基础读写放大问题。",
            ]
        ),
        "internship": resume_item(
            "京东",
            "数据库中间件实习生",
            "2024.06—2024.12",
            [
                "\\textbf{职责}: 分片键迁移方案评估与双写校验工具。",
                "\\textbf{成果}: 灰度窗口内数据不一致行数 <0.001\\%。",
            ],
        ),
        "projects": resume_item(
            "慢查询根因分析工具",
            "实验室课题",
            "2024.01—2024.08",
            [
                "基于 Performance Schema 聚类，误报率较规则引擎下降 35\\%。",
            ],
        ),
        "honors": itemize_lines(["哈工大 优秀团员", "中国数据库技术大会 DTCC 学生票分享"]),
    },
    {
        "file": "tang_li",
        "name": "唐莉",
        "school_line": "清华大学 | 电子信息 · 硕士 | 2023—2026",
        "email": "tangli@tsinghua.edu.cn",
        "phone": "138-0017-0017",
        "summary": "推荐系统与排序模型，熟悉 PyTorch、DeepFM 与多任务学习；在离线 AUC 提升 0.018，线上 CTR +4.5%。",
        "education": resume_item(
            "清华大学",
            "电子工程系 | 电子信息 | 硕士",
            "2023.09—2026.06(预计)",
            ["导师组：机器学习与推荐。"],
        ),
        "skills": itemize_lines(
            [
                "熟悉 Python、Spark、特征工程与离线评估（AUC、GAUC）。",
                "掌握 Wide\\&Deep、DeepFM、DIN 等排序模型。",
                "了解 TensorFlow Serving 与 A/B 实验平台对接。",
            ]
        ),
        "internship": resume_item(
            "快手",
            "推荐算法实习生",
            "2024.07—2024.12",
            [
                "\\textbf{职责}: 短视频粗排模型特征与负采样策略迭代。",
                "\\textbf{成果}: 离线 Recall@100 提升 2.3\\%，线上时长 +1.2\\%。",
            ],
        ),
        "projects": resume_item(
            "多兴趣召回模块",
            "科研助理项目",
            "2024.02—2024.08",
            [
                "胶囊网络思想做兴趣向量拆分，长尾作者曝光 +8\\%。",
            ],
        ),
        "honors": itemize_lines(["清华大学 综合优秀奖学金", "Kaggle 竞赛 Notebook 银牌区"]),
    },
    {
        "file": "gao_peng",
        "name": "高鹏",
        "school_line": "国防科技大学 | 计算机科学与技术 · 学士 | 2020—2024",
        "email": "gaopeng@nudt.edu.cn",
        "phone": "138-0018-0018",
        "summary": "高性能 C++ 与低延迟系统，熟悉无锁队列、内存池与 CPU 亲和性；量化回测引擎单线程延迟优化 30%。",
        "education": resume_item(
            "国防科技大学",
            "计算机学院 | 计算机科学与技术 | 学士",
            "2020.09—2024.06",
            ["高性能计算选修与竞赛训练。"],
        ),
        "skills": itemize_lines(
            [
                "精通 C++17、多线程、模板元编程与 perf 火焰图分析。",
                "熟悉 Linux epoll、零拷贝与 DPDK 入门。",
                "了解 FIX 协议与回测撮合仿真基础。",
            ]
        ),
        "internship": resume_item(
            "某量化私募",
            "C++ 开发实习生",
            "2024.03—2024.08",
            [
                "\\textbf{职责}: 行情接入与订单路由模块性能剖析。",
                "\\textbf{成果}: 关键路径指令数减少 12\\%（llvm-mca 辅助）。",
            ],
        ),
        "projects": resume_item(
            "内存池化订单簿",
            "毕业设计",
            "2023.10—2024.05",
            [
                "预分配 slab，碎片率 <3\\%，压测下抖动方差下降 40\\%。",
            ],
        ),
        "honors": itemize_lines(["ACM-ICPC 亚洲区域赛 银牌", "国防科大 优秀学员"]),
    },
    {
        "file": "bai_rui",
        "name": "白锐",
        "school_line": "华南理工大学 | 软件工程 · 学士 | 2021—2025",
        "email": "bairui@scut.edu.cn",
        "phone": "138-0019-0019",
        "summary": "跨平台 Flutter 与移动端工程化，熟悉 Dart、Provider 与混合栈通信；完成企业内部考勤 App 双端交付。",
        "education": resume_item(
            "华南理工大学",
            "软件学院 | 软件工程 | 学士",
            "2021.09—2025.06",
            ["移动开发与人机交互课程。"],
        ),
        "skills": itemize_lines(
            [
                "熟悉 Flutter、Dart、Riverpod/Provider 状态管理。",
                "掌握 Platform Channel 与原生地图 SDK 集成。",
                "了解 CI 双端打包与 Firebase Crashlytics。",
            ]
        ),
        "internship": resume_item(
            "顺丰科技",
            "移动端开发实习生",
            "2024.06—2024.12",
            [
                "\\textbf{职责}: 小哥端扫描模块 Flutter 重构。",
                "\\textbf{成果}: 扫码页崩溃率下降 60\\%，包体增加 <800KB。",
            ],
        ),
        "projects": resume_item(
            "Flutter 插件：蓝牙打印",
            "pub.dev",
            "2023.08—2024.01",
            [
                "likes 200+，支持 ESC/POS 常用指令子集。",
            ],
        ),
        "honors": itemize_lines(["广东省大学生计算机设计大赛 一等奖", "华南理工 三好学生"]),
    },
    {
        "file": "dong_mei",
        "name": "董梅",
        "school_line": "中国人民大学 | 信息管理与信息系统 · 硕士 | 2022—2025",
        "email": "dongmei@ruc.edu.cn",
        "phone": "138-0020-0020",
        "summary": "技术型产品经理，熟悉 SQL、埋点体系与 PRD 评审；推动搜索排序策略需求从评审到上线周期缩短 25%。",
        "education": resume_item(
            "中国人民大学",
            "信息学院 | 信息管理与信息系统 | 硕士",
            "2022.09—2025.06",
            ["数字化治理与数据分析方向。"],
        ),
        "skills": itemize_lines(
            [
                "熟悉 Axure/Figma、SQL、A/B 实验设计与漏斗分析。",
                "掌握 Python 数据处理与简单自动化报表。",
                "了解微服务边界与接口文档（OpenAPI）协作。",
            ]
        ),
        "internship": resume_item(
            "滴滴出行",
            "产品实习生（技术中台方向）",
            "2024.06—2024.12",
            [
                "\\textbf{职责}: 司机端增长活动配置平台需求管理与验收。",
                "\\textbf{成果}: 需求返工率从 18\\% 降至 9\\%。",
            ],
        ),
        "projects": resume_item(
            "指标体系白皮书整理",
            "校内课题",
            "2024.02—2024.06",
            [
                "梳理 120+ 核心指标口径，被课题组采纳为基线文档。",
            ],
        ),
        "honors": itemize_lines(["中国人民大学 优秀学生干部", "互联网+ 校赛 金奖"]),
    },
    {
        "file": "qian_feng",
        "name": "钱峰",
        "school_line": "北京邮电大学 | 网络工程 · 学士 | 2020—2024",
        "email": "qianfeng@bupt.edu.cn",
        "phone": "138-0021-0021",
        "summary": "爬虫与反爬对抗，熟悉 Scrapy、Playwright 与 TLS 指纹；建设合规采集管线，请求成功率从 71% 提升至 94%。",
        "education": resume_item(
            "北京邮电大学",
            "计算机学院 | 网络工程 | 学士",
            "2020.09—2024.06",
            ["网络协议与系统安全课程为主。"],
        ),
        "skills": itemize_lines(
            [
                "熟悉 Python、Scrapy、Redis 去重与分布式调度。",
                "掌握 Playwright、代理池轮换与验证码打码平台对接（合规场景）。",
                "了解 JA3 指纹与 HTTP/2 帧级调试。",
            ]
        ),
        "internship": resume_item(
            "某数据服务商",
            "数据采集实习生",
            "2024.01—2024.08",
            [
                "\\textbf{职责}: 电商价格监控链路稳定性。",
                "\\textbf{成果}: 日级任务失败重跑率下降 52\\%。",
            ],
        ),
        "projects": resume_item(
            "合规 Robots 解析器",
            "毕业设计",
            "2023.10—2024.05",
            [
                "支持多级 robots.txt 缓存与 TTL，误判拦截率 <0.1\\%。",
            ],
        ),
        "honors": itemize_lines(["北邮 优秀毕业生", "全国大学生信息安全竞赛 华北三等奖"]),
    },
    {
        "file": "xie_bo",
        "name": "谢波",
        "school_line": "四川大学 | 软件工程 · 硕士 | 2023—2026",
        "email": "xiebo@scu.edu.cn",
        "phone": "138-0022-0022",
        "summary": "音视频与 FFmpeg，熟悉 H.264/HEVC 封装、硬编解码与 QoS；直播推流端卡顿率（卡顿时长占比）降低 0.7pp。",
        "education": resume_item(
            "四川大学",
            "计算机学院 | 软件工程 | 硕士",
            "2023.09—2026.06(预计)",
            ["多媒体技术实验室。"],
        ),
        "skills": itemize_lines(
            [
                "熟悉 C/C++、FFmpeg API、MediaCodec/VideoToolbox。",
                "掌握 RTMP/HLS、码率自适应与弱网重传策略。",
                "了解 WebRTC 信令与 STUN/TURN 基础。",
            ]
        ),
        "internship": resume_item(
            "B站",
            "音视频工程实习生",
            "2024.07—2024.12",
            [
                "\\textbf{职责}: 移动端直播 SDK 功耗与发热优化。",
                "\\textbf{成果}: 同等画质下平均码率下降 8\\%，CPU 占用下降 6pt。",
            ],
        ),
        "projects": resume_item(
            "实时美颜滤镜链",
            "课题 Demo",
            "2024.02—2024.06",
            [
                "GPU Shader + FFmpeg filter 组合，端到端延迟 +12ms。",
            ],
        ),
        "honors": itemize_lines(["四川大学 优秀研究生", "中国高校计算机大赛 智能交互创新赛 三等奖"]),
    },
    {
        "file": "jiang_nan",
        "name": "江南",
        "school_line": "天津大学 | 集成电路工程 · 硕士 | 2022—2025",
        "email": "jiangnan@tju.edu.cn",
        "phone": "138-0023-0023",
        "summary": "数字 IC 与 EDA 脚本，熟悉 Verilog、时序约束与 Python 批处理；参与 FPGA 原型验证与综合脚本维护。",
        "education": resume_item(
            "天津大学",
            "微电子学院 | 集成电路工程 | 硕士",
            "2022.09—2025.06",
            ["数字系统设计与验证方向。"],
        ),
        "skills": itemize_lines(
            [
                "熟悉 Verilog、SystemVerilog 断言入门、Vivado/Quartus。",
                "掌握 Tcl/Python 自动化综合与报告解析。",
                "了解跨时钟域 CDC 与 STA 基础。",
            ]
        ),
        "internship": resume_item(
            "某芯片设计公司",
            "数字验证实习生",
            "2024.06—2024.12",
            [
                "\\textbf{职责}: AXI-lite 从设备 UVM 环境搭建与用例补充。",
                "\\textbf{成果}: 功能覆盖率从 82\\% 提升至 96\\%。",
            ],
        ),
        "projects": resume_item(
            "RISC-V 单周期 CPU",
            "课程大作业",
            "2023.09—2024.01",
            [
                "支持 RV32I 子集，通过 200+ 汇编自测用例。",
            ],
        ),
        "honors": itemize_lines(["集创赛 华北赛区 二等奖", "天津大学 学业奖学金"]),
    },
    {
        "file": "tang_wei",
        "name": "汤伟",
        "school_line": "山东大学 | 计算机科学与技术 · 学士 | 2021—2025",
        "email": "tangwei@sdu.edu.cn",
        "phone": "138-0024-0024",
        "summary": "Linux 运维与自动化，熟悉 Ansible、Terraform 与 ELK；将虚拟机交付从手工 2h 降至 IaC 15min。",
        "education": resume_item(
            "山东大学",
            "计算机科学与技术学院 | 计算机科学与技术 | 学士",
            "2021.09—2025.06",
            ["云计算与数据中心课程。"],
        ),
        "skills": itemize_lines(
            [
                "熟悉 Linux、Shell、Ansible、Terraform、GitLab CI。",
                "掌握 ELK、Filebeat 与日志解析 Grok。",
                "了解 VMware/KVM 与基础网络 ACL。",
            ]
        ),
        "internship": resume_item(
            "浪潮",
            "运维开发实习生",
            "2024.07—2024.12",
            [
                "\\textbf{职责}: 政务云租户资源巡检与告警降噪。",
                "\\textbf{成果}: 月均无效告警条数下降 38\\%。",
            ],
        ),
        "projects": resume_item(
            "Ansible Role 仓库",
            "开源",
            "2024.01—2024.06",
            [
                "标准化中间件安装，被学院实验室 4 个课题组复用。",
            ],
        ),
        "honors": itemize_lines(["山东省大学生科技创新大赛 三等奖", "山东大学 社会实践先进个人"]),
    },
    {
        "file": "han_lu",
        "name": "韩露",
        "school_line": "浙江大学 | 工业设计（智能设计）· 学士 | 2021—2025",
        "email": "hanlu@zju.edu.cn",
        "phone": "138-0025-0025",
        "summary": "计算机图形学与 WebGL，熟悉 Three.js、着色器与 PBR 材质；Web 端数字孪生场景帧率稳定在 45 FPS。",
        "education": resume_item(
            "浙江大学",
            "计算机学院 | 工业设计（智能设计）| 学士",
            "2021.09—2025.06",
            ["交叉方向：人机交互与图形学。"],
        ),
        "skills": itemize_lines(
            [
                "熟悉 JavaScript、TypeScript、Three.js、GLSL。",
                "掌握 glTF、Draco 压缩与实例化绘制优化。",
                "了解 WebGPU 与 Babylon.js 入门实验。",
            ]
        ),
        "internship": resume_item(
            "阿里云 | 视觉计算",
            "图形渲染实习生",
            "2024.06—2024.12",
            [
                "\\textbf{职责}: 三维园区编辑器性能剖析与 LOD 策略。",
                "\\textbf{成果}: 同屏三角面数上限提升约 2.1 倍仍保持可交互。",
            ],
        ),
        "projects": resume_item(
            "WebGL 体素地形",
            "毕设",
            "2024.02—2024.06",
            [
                "Chunk 加载 + 视锥裁剪，内存峰值控制在 1.2GB 内。",
            ],
        ),
        "honors": itemize_lines(["中国好设计奖 学生组 提名", "浙江大学 研究与创新奖学金"]),
    },
    {
        "file": "cai_jun",
        "name": "蔡俊",
        "school_line": "上海财经大学 | 金融数学 · 硕士 | 2022—2025",
        "email": "caijun@mail.shufe.edu.cn",
        "phone": "138-0026-0026",
        "summary": "量化研究与 Python 工程，熟悉 Pandas、回测框架与风控指标；期货 CTA 策略样本外夏普 1.4（仿真盘）。",
        "education": resume_item(
            "上海财经大学",
            "数学学院 | 金融数学 | 硕士",
            "2022.09—2025.06",
            ["交叉选修：机器学习与程序设计。"],
        ),
        "skills": itemize_lines(
            [
                "熟悉 Python、NumPy、Pandas、Cython 热点函数加速。",
                "掌握向量化回测、滑价与手续费模型。",
                "了解 Linux 定时任务与数据落盘校验。",
            ]
        ),
        "internship": resume_item(
            "某券商自营",
            "量化研究实习生",
            "2024.07—2024.12",
            [
                "\\textbf{职责}: 商品期货因子挖掘与组合优化。",
                "\\textbf{成果}: 新因子组合在仿真盘最大回撤下降 1.8pt。",
            ],
        ),
        "projects": resume_item(
            "事件驱动回测引擎",
            "课题代码",
            "2024.01—2024.06",
            [
                "日级 K 线回测速度 120 万 bar/min（单进程）。",
            ],
        ),
        "honors": itemize_lines(["全国研究生数学建模竞赛 一等奖", "上财 优秀学生"]),
    },
    {
        "file": "peng_yu",
        "name": "彭宇",
        "school_line": "中国科学院大学 | 网络空间安全 · 硕士 | 2023—2026",
        "email": "pengyu@ucas.ac.cn",
        "phone": "138-0027-0027",
        "summary": "隐私计算与联邦学习，熟悉 PySyft 思想、秘密分享与安全聚合；横向联邦图像分类在 Non-IID 下准确率损失 <2%。",
        "education": resume_item(
            "中国科学院大学",
            "网络空间安全学院 | 网络空间安全 | 硕士",
            "2023.09—2026.06(预计)",
            ["研究所：信息工程研究所（虚构组名略）。"],
        ),
        "skills": itemize_lines(
            [
                "熟悉 Python、PyTorch、差分隐私基础与 DP-SGD。",
                "掌握安全聚合（SecAgg）与同态加密入门实验。",
                "了解 MPC 协议仿真与通信轮次分析。",
            ]
        ),
        "internship": resume_item(
            "蚂蚁集团 | 隐私计算",
            "研究型实习生",
            "2024.06—2024.12",
            [
                "\\textbf{职责}: 纵向联邦特征对齐模块原型验证。",
                "\\textbf{成果}: PSI 匹配耗时在 100 万级 ID 场景 <90s（内网）。",
            ],
        ),
        "projects": resume_item(
            "联邦学习仿真平台",
            "实验室项目",
            "2024.02—2024.08",
            [
                "支持 10 客户端异步聚合，收敛曲线与中心化基线对齐度 0.93。",
            ],
        ),
        "honors": itemize_lines(["中国科学院大学 三好学生", "密码创新竞赛 优胜奖"]),
    },
    {
        "file": "lu_kai",
        "name": "陆凯",
        "school_line": "重庆大学 | 物联网工程 · 学士 | 2020—2024",
        "email": "lukai@cqu.edu.cn",
        "phone": "138-0028-0028",
        "summary": "边缘计算与 IoT 平台，熟悉 MQTT、KubeEdge 与设备孪生；园区路灯边缘网关规则引擎 CPU 占用下降 19%。",
        "education": resume_item(
            "重庆大学",
            "微电子与通信工程学院 | 物联网工程 | 学士",
            "2020.09—2024.06",
            ["嵌入式与通信协议课程。"],
        ),
        "skills": itemize_lines(
            [
                "熟悉 Go、MQTT、EMQX 规则引擎与 TimescaleDB。",
                "掌握 Docker、KubeEdge 云边协同部署。",
                "了解 Modbus/Bacnet 与 OPC UA 网关桥接。",
            ]
        ),
        "internship": resume_item(
            "海尔智家",
            "IoT 平台实习生",
            "2024.03—2024.08",
            [
                "\\textbf{职责}: 设备影子同步延迟监控与告警。",
                "\\textbf{成果}: P99 延迟从 1.4s 降至 0.6s（华东区抽样）。",
            ],
        ),
        "projects": resume_item(
            "边缘规则热更新",
            "毕业设计",
            "2023.10—2024.05",
            [
                "基于 WebAssembly 沙箱执行用户脚本，崩溃隔离率 100\\%。",
            ],
        ),
        "honors": itemize_lines(["挑战杯 重庆市特等奖", "重庆大学 优秀本科毕业生"]),
    },
    {
        "file": "xiong_bing",
        "name": "熊兵",
        "school_line": "吉林大学 | 车辆工程（智能网联）· 硕士 | 2022—2025",
        "email": "xiongbing@jlu.edu.cn",
        "phone": "138-0029-0029",
        "summary": "自动驾驶感知与深度学习，熟悉 BEVDet、OpenPCDet 与数据闭环；在 KITTI 子集上 3D AP 提升 4.1%。",
        "education": resume_item(
            "吉林大学",
            "汽车工程学院 | 车辆工程（智能网联）| 硕士",
            "2022.09—2025.06",
            ["导师方向：环境感知与传感器融合。"],
        ),
        "skills": itemize_lines(
            [
                "熟悉 Python、PyTorch、点云处理与 Camera-Lidar 标定。",
                "掌握 BEV 表征、数据增强与混合精度训练。",
                "了解 ONNX 导出与 TensorRT INT8 PTQ 流程。",
            ]
        ),
        "internship": resume_item(
            "Momenta",
            "感知算法实习生",
            "2024.06—2024.12",
            [
                "\\textbf{职责}: 夜间场景检测长尾类别数据挖掘。",
                "\\textbf{成果}: 夜间行人 Recall@0.8IoU 提升 6pt。",
            ],
        ),
        "projects": resume_item(
            "半自动标注流水线",
            "校企课题",
            "2024.01—2024.08",
            [
                "主动学习挑选帧，人工标注成本下降约 35\\%。",
            ],
        ),
        "honors": itemize_lines(["中国智能汽车大赛 东北赛区 二等奖", "吉林大学 学业奖学金"]),
    },
    {
        "file": "feng_qi",
        "name": "冯祺",
        "school_line": "南开大学 | 计算机科学与技术 · 硕士 | 2023—2026",
        "email": "fengqi@nankai.edu.cn",
        "phone": "138-0030-0030",
        "summary": "编译器与程序分析，熟悉 LLVM IR、Clang AST 与静态检查规则开发；为课程编译器实现 SSA 与简单寄存器分配。",
        "education": resume_item(
            "南开大学",
            "计算机学院 | 计算机科学与技术 | 硕士",
            "2023.09—2026.06(预计)",
            ["研究方向：程序语言与编译优化。"],
        ),
        "skills": itemize_lines(
            [
                "熟悉 C++、LLVM、Clang LibTooling、CMake。",
                "掌握数据流分析、别名分析与简单误报抑制策略。",
                "了解 WebAssembly 与 wasm-opt 管道实验。",
            ]
        ),
        "internship": resume_item(
            "华为2012实验室",
            "编译器开发实习生",
            "2024.07—2024.12",
            [
                "\\textbf{职责}: 特定内建函数向量化模式匹配 pass。",
                "\\textbf{成果}: SPEC CPU 子项几何均值 +1.7\\%（内部分支）。",
            ],
        ),
        "projects": resume_item(
            "教学用 SysY 编译器",
            "课程大作业",
            "2024.02—2024.06",
            [
                "支持 -O2 常量折叠与死代码消除，自测通过率 100\\%。",
            ],
        ),
        "honors": itemize_lines(["CCF 优秀大学生奖（候选展示用）", "南开大学 优秀学生奖学金"]),
    },
]


def main() -> None:
    out_dir = Path(__file__).resolve().parent
    assert len(PROFILES) == 30, len(PROFILES)
    for p in PROFILES:
        fields = {k: p[k] for k in (
            "name", "phone", "email", "school_line", "summary",
            "education", "skills", "internship", "projects", "honors",
        )}
        ext = _extras_for(p["file"])
        fields["education_extra"] = ext["education_extra"]
        fields["internship2"] = ext["internship2"]
        fields["projects2"] = ext["projects2"]
        fields["summary"] = esc(p["summary"] + SUMMARY_SUPPLEMENT)
        fields["skills"] = (p["skills"].rstrip() + "\n" + itemize_lines(SKILL_TAIL_LINES))
        fields["honors"] = (p["honors"].rstrip() + "\n" + itemize_lines(HONOR_TAIL_LINES))
        tex = PREAMBLE % fields
        path = out_dir / f"{p['file']}.tex"
        path.write_text(tex, encoding="utf-8")
        print(path)


if __name__ == "__main__":
    main()
