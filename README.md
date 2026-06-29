# AgentRecruit 多智能体招聘系统

AgentRecruit 是一个面向招聘场景的多智能体系统，围绕 JD 管理、候选人管理、简历解析、智能匹配、匹配审核和招聘数据看板构建完整工作流。系统采用前后端分离架构，Java 负责业务后端，Python 负责 AI 能力，React 负责管理端交互界面。

## 项目展示

- 演示视频：[在这里添加系统演示视频](docs/assets/demo-video.mp4)
<img width="947" height="499" alt="img" src="https://github.com/user-attachments/assets/e21e8509-1651-445e-a88c-f5b6cd0f2ce1" />


## 核心功能

### Dashboard

提供招聘业务的整体概览，包括活跃 JD、候选人数量、待审核任务和近期趋势，帮助 HR 快速了解当前招聘进展。

### JD 管理

支持创建、编辑、删除和状态维护 JD。新建 JD 时可以选择岗位模板，也可以手动填写岗位信息、技能要求、薪资范围和职位描述。JD 状态可在列表操作中维护，便于区分发布中、暂停、关闭等不同阶段。

### 候选人管理

支持候选人列表管理、简历上传、批量上传、异步解析和删除操作。上传后的简历会进入后台解析流程，系统提取候选人基础信息、技能、经验和教育背景，为后续智能匹配提供结构化数据。

### 智能匹配

支持基于 JD 条件发起候选人匹配，可按岗位、关键词、匹配数量等条件筛选。AI 端结合 JD 要求、候选人简历内容和向量检索结果生成匹配建议，帮助 HR 快速定位合适候选人。

### 匹配历史

记录每次匹配任务的结果和审核状态。HR 可以查看岗位下的候选人匹配明细、匹配分数、推荐理由和原始简历 PDF，并对匹配结果进行审核、修改、删除和查询。

### 设置中心

提供系统偏好配置和账号相关设置，包括智能匹配人数、默认审核偏好、通知偏好、密码修改等基础能力。

## 技术栈

### 前端

- React 19
- TypeScript
- Vite
- Tailwind CSS
- TanStack Query
- TanStack Table
- React Router
- Recharts
- Lucide React

前端负责系统管理界面、表格交互、筛选查询、弹窗表单、审核页面和数据可视化展示。

### Java 业务后端

- Java 17
- Spring Boot 3
- Spring Security
- MyBatis-Plus
- MySQL
- Redis
- WebFlux
- Knife4j
- PDFBox

Java 后端负责账号认证、业务数据管理、JD 管理、候选人管理、匹配记录、审核流程、文件管理和与 AI 服务的业务编排。

### Python AI 服务

- Python
- FastAPI
- LangGraph
- LangChain
- OpenAI-Compatible LLM
- Milvus 向量数据库
- LangSmith 可观测性
- PyMuPDF / python-docx

Python AI 服务负责简历解析、候选人画像生成、JD 与候选人的智能匹配、招聘报告生成、向量检索和多 Agent 工作流编排。

## 目录结构

```text
agent-recruit/
├── frontend/       # React 管理端
├── java-backend/   # Java Spring Boot 业务后端
├── api/            # Python AI 服务入口
├── agent/          # 多 Agent 工作流与工具
├── rag/            # 向量检索与重排能力
├── skills/         # 招聘场景技能定义
├── data/           # 简历、向量数据和记忆数据
└── docs/           # 项目文档与展示素材
```

## 本地运行

### 前端

```bash
cd frontend
npm install
npm run dev
```

### Java 后端

```bash
cd java-backend
mvn spring-boot:run
```

### Python AI 服务

```bash
pip install -r requirements.txt
uvicorn api.server:app --host 0.0.0.0 --port 8008
```

## 产品目标

AgentRecruit 的目标不是简单记录招聘信息，而是把招聘流程中的重复判断、简历阅读、岗位匹配和结果审核连接成一个更高效的智能工作台。HR 可以在同一个系统里完成岗位维护、候选人导入、AI 推荐、人工审核和历史追踪，让招聘决策更快、更清晰、更可复盘。
