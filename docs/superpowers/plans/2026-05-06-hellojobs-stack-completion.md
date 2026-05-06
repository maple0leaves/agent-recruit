# HelloJobs Stack Completion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 `hellojobs` 从“可运行的 AI 招聘 MVP”补齐为“可部署、可验证、可演示的标准全栈项目”。

**Architecture:** 保持现有 `React + FastAPI + SQLAlchemy + LangGraph` 主架构不变，只补工程化底座。优先补数据库、容器化、CI、测试和质量工具，避免大规模重写业务逻辑。

**Tech Stack:** React 19, TypeScript, Vite, Tailwind CSS 4, FastAPI, SQLAlchemy Async, Alembic, PostgreSQL, Docker, GitHub Actions, Pytest, Vitest, Playwright, Ruff, Redis(optional), Celery(optional)

---

## Scope

本计划分两段执行：

1. **最小补完方案（1 周内）**
   - PostgreSQL 支持
   - Docker / Compose
   - GitHub Actions
   - Python 质量工具
   - Frontend 单测基础

2. **标准补完方案（2-3 周）**
   - Playwright E2E
   - Redis + 异步任务雏形
   - MinIO / 对象存储抽象
   - Sentry / 监控
   - RBAC 与运维增强

---

### Task 1: PostgreSQL Production Path

**Files:**
- Modify: `hellojobs/config.py`
- Modify: `hellojobs/backend/db/engine.py`
- Modify: `hellojobs/README.md`
- Modify: `hellojobs/.env.example`
- Create: `hellojobs/backend/db/migrations/versions/<timestamp>_baseline_prod_ready.py`（仅当现有迁移不完整时）
- Test: `hellojobs/tests/conftest.py`

- [ ] **Step 1: 明确数据库运行模式**

保留本地 `SQLite` 默认值，但让 README 和 `.env.example` 明确支持：

```ini
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/hellojobs
```

- [ ] **Step 2: 增加 PostgreSQL 驱动依赖**

在 `requirements.txt` 增加：

```txt
asyncpg>=0.29.0
```

- [ ] **Step 3: 校验 SQLAlchemy 引擎兼容性**

确认 `backend/db/engine.py` 不写死 SQLite 特性，继续保持：

```python
engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
```

- [ ] **Step 4: 补充本地与生产两套示例配置**

在 `.env.example` 中给出两套注释配置：

```ini
# Local
# DATABASE_URL=sqlite+aiosqlite:///./data/dev.db

# Production / Docker
# DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/hellojobs
```

- [ ] **Step 5: 验证测试仍可走 SQLite**

运行：

```bash
pytest hellojobs/tests -q
```

预期：测试继续使用 `tests/conftest.py` 中的临时 SQLite，不受 Postgres 支持新增影响。

---

### Task 2: Dockerize Backend + Frontend Delivery

**Files:**
- Create: `hellojobs/Dockerfile`
- Create: `hellojobs/docker-compose.yml`
- Create: `hellojobs/.dockerignore`
- Modify: `hellojobs/README.md`
- Modify: `hellojobs/frontend/vite.config.ts`

- [ ] **Step 1: 编写多阶段 Dockerfile**

建议结构：

```dockerfile
FROM node:20 AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.11-slim AS app
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
COPY --from=frontend-builder /app/static ./static
CMD ["uvicorn", "api.server:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 2: 编写 compose 编排**

至少包含：

```yaml
services:
  app:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    depends_on:
      - db

  db:
    image: postgres:16
    environment:
      POSTGRES_DB: hellojobs
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
```

- [ ] **Step 3: 规范静态资源构建路径**

确认 `frontend/vite.config.ts` 的：

```ts
build: {
  outDir: "../static",
  emptyOutDir: true,
}
```

与 Docker 多阶段构建一致，不需要再额外手工复制。

- [ ] **Step 4: 补充一键启动文档**

README 增加：

```bash
docker compose up --build
```

以及首次初始化说明：

```bash
docker compose exec app alembic upgrade head
docker compose exec app python -m backend.db.seed
```

---

### Task 3: CI Pipeline

**Files:**
- Create: `hellojobs/.github/workflows/ci.yml`
- Modify: `hellojobs/README.md`

- [ ] **Step 1: 建立最小 CI 工作流**

工作流包含：

```yaml
name: CI

on:
  push:
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
      - run: pip install -r requirements.txt
      - run: pytest tests -q
      - run: cd frontend && npm ci && npm run lint && npm run build
```

- [ ] **Step 2: 增加 Docker build smoke test**

在后续 job 增加：

```yaml
  docker:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: docker build -t hellojobs .
```

- [ ] **Step 3: 在 README 中声明质量门禁**

补一句：

```md
每次提交会自动执行后端测试、前端 lint/build 与 Docker 构建校验。
```

---

### Task 4: Python Quality Tooling

**Files:**
- Modify: `hellojobs/requirements.txt`
- Create: `hellojobs/pyproject.toml`
- Create: `hellojobs/.pre-commit-config.yaml`
- Modify: `hellojobs/README.md`

- [ ] **Step 1: 增加 Python 工程工具**

在 `requirements.txt` 或开发依赖中补：

```txt
ruff>=0.6.0
pre-commit>=3.8.0
```

- [ ] **Step 2: 配置 Ruff**

在 `pyproject.toml` 中加入：

```toml
[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B"]
```

- [ ] **Step 3: 配置 pre-commit**

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.6.9
    hooks:
      - id: ruff
      - id: ruff-format
```

- [ ] **Step 4: README 增加开发规范**

```bash
pre-commit install
ruff check .
ruff format .
```

---

### Task 5: Frontend Unit Test Foundation

**Files:**
- Modify: `hellojobs/frontend/package.json`
- Create: `hellojobs/frontend/vitest.config.ts`
- Create: `hellojobs/frontend/src/test/setup.ts`
- Create: `hellojobs/frontend/src/components/ProtectedRoute.test.tsx`
- Create: `hellojobs/frontend/src/pages/Login.test.tsx`

- [ ] **Step 1: 增加测试依赖**

前端补充：

```json
{
  "devDependencies": {
    "vitest": "...",
    "@testing-library/react": "...",
    "@testing-library/jest-dom": "...",
    "@testing-library/user-event": "...",
    "jsdom": "..."
  }
}
```

- [ ] **Step 2: 增加测试脚本**

```json
"scripts": {
  "test": "vitest run",
  "test:watch": "vitest"
}
```

- [ ] **Step 3: 建立测试入口**

`src/test/setup.ts`：

```ts
import "@testing-library/jest-dom";
```

- [ ] **Step 4: 优先覆盖 2 个最高价值场景**

测试点：
- `ProtectedRoute`：未登录跳转 `/login`
- `Login`：提交表单时触发登录流程

- [ ] **Step 5: 在 CI 中接入前端 test**

把 CI 改成：

```bash
cd frontend && npm ci && npm run lint && npm run test && npm run build
```

---

### Task 6: Playwright E2E Main Flow

**Files:**
- Create: `hellojobs/frontend/playwright.config.ts`
- Create: `hellojobs/frontend/e2e/login-and-jd.spec.ts`
- Modify: `hellojobs/frontend/package.json`
- Modify: `hellojobs/README.md`

- [ ] **Step 1: 增加 Playwright**

补依赖与脚本：

```json
"scripts": {
  "e2e": "playwright test"
}
```

- [ ] **Step 2: 只做 1 条黄金路径**

覆盖流程：
1. 登录
2. 打开 JD 管理
3. 创建 JD
4. 列表看到新建 JD

- [ ] **Step 3: 控制范围**

第一版不要把 SSE 匹配也塞进 E2E，先把最稳定的 CRUD 链路跑通。

---

### Task 7: Redis + Async Job Skeleton

**Files:**
- Create: `hellojobs/backend/tasks/__init__.py`
- Create: `hellojobs/backend/tasks/celery_app.py`
- Create: `hellojobs/backend/tasks/jobs.py`
- Modify: `hellojobs/config.py`
- Modify: `hellojobs/backend/api/routes/candidate.py`
- Modify: `hellojobs/api/server.py`
- Modify: `hellojobs/docker-compose.yml`

- [ ] **Step 1: 只做任务底座，不立刻全量迁移**

先把这些高耗时任务定义为候选异步任务：
- 简历解析
- 向量索引重建
- 导出报告

- [ ] **Step 2: 增加基础配置**

```ini
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
```

- [ ] **Step 3: compose 补 Redis**

```yaml
  redis:
    image: redis:7
    ports:
      - "6379:6379"
```

- [ ] **Step 4: 先迁移 rebuild-index**

`/api/admin/rebuild-index` 最适合先改成异步任务提交接口，因为它本身是后台任务，不强依赖同步返回。

---

### Task 8: Object Storage Abstraction

**Files:**
- Create: `hellojobs/backend/storage/__init__.py`
- Create: `hellojobs/backend/storage/local.py`
- Create: `hellojobs/backend/storage/s3.py`
- Modify: `hellojobs/backend/api/routes/candidate.py`
- Modify: `hellojobs/config.py`

- [ ] **Step 1: 抽象文件存储接口**

至少统一出：

```python
class StorageBackend:
    async def save(self, file_name: str, content: bytes) -> str: ...
```

- [ ] **Step 2: 默认仍然走本地存储**

先不破坏现有 `data/resumes` 逻辑，只把“保存文件”从路由里抽出来。

- [ ] **Step 3: 为 MinIO / S3 预留实现**

生产时再启用对象存储，无需重构业务层。

---

### Task 9: Observability and Error Hardening

**Files:**
- Modify: `hellojobs/api/server.py`
- Modify: `hellojobs/backend/api/routes/auth.py`
- Modify: `hellojobs/config.py`
- Create: `hellojobs/backend/observability/sentry.py`

- [ ] **Step 1: 收紧错误返回**

把类似：

```python
raise HTTPException(status_code=500, detail=str(e))
```

调整为：

```python
logger.exception("Recruitment workflow failed")
raise HTTPException(status_code=500, detail="服务内部错误，请稍后重试")
```

- [ ] **Step 2: 生产化 cookie 配置**

把：

```python
secure=False
```

改为环境变量驱动。

- [ ] **Step 3: 接入 Sentry（可选开关）**

增加：

```ini
SENTRY_DSN=
SENTRY_ENVIRONMENT=development
```

---

### Task 10: RBAC and Production Guardrails

**Files:**
- Modify: `hellojobs/backend/api/deps.py`
- Modify: `hellojobs/backend/db/models/user.py`
- Modify: `hellojobs/backend/api/routes/*.py`
- Create: `hellojobs/tests/test_rbac.py`

- [ ] **Step 1: 先抽角色检查依赖**

比如：

```python
def require_role(*roles: str):
    ...
```

- [ ] **Step 2: 第一版只区分 Admin / HR**

不要一开始就做太复杂的权限矩阵。

- [ ] **Step 3: 优先保护管理接口**

至少限制：
- `admin/rebuild-index`
- 候选人状态变更
- JD 状态变更

---

## Recommended Execution Order

### 一周最小补完

1. Task 1 PostgreSQL
2. Task 2 Docker
3. Task 3 CI
4. Task 4 Python Quality
5. Task 5 Frontend Unit Test

### 两到三周标准补完

6. Task 6 Playwright
7. Task 9 Error Hardening / Observability
8. Task 7 Redis + Async Job Skeleton
9. Task 8 Object Storage
10. Task 10 RBAC

---

## Delivery Milestones

### Milestone A: 可演示全栈项目

完成后应满足：
- 本地一条命令启动
- 新人能按 README 跑起来
- CI 自动校验基本质量
- 前后端至少有基础自动化测试
- 数据库可切换到 PostgreSQL

### Milestone B: 可扩展产品雏形

完成后应满足：
- 有异步任务通道
- 文件存储可切对象存储
- 有基础监控与错误追踪
- 有最小角色权限模型

---

## Notes

- 当前最不建议做的事：重写前端、替换 FastAPI、替换 LangGraph。这些都不是短板。
- 当前最该做的事：补工程底座，而不是继续叠加业务页面。
