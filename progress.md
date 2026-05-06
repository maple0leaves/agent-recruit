# Progress

## 2026-05-06

- 保存了最小全栈交付设计文档：`docs/superpowers/specs/2026-05-06-hellojobs-min-fullstack-design.md`
- 建立了项目级计划文件：`task_plan.md`
- 记录了关键发现：现有后端测试与实际 `/api` 路由前缀不一致
- 选定第一项实现任务：修复后端测试路径并运行关键测试
- 修复了 `tests/test_auth.py`、`tests/test_jd.py`、`tests/test_candidate.py`、`tests/test_sse.py` 的旧接口路径
- 在 `hellojobs` 环境中运行关键后端测试，结果为 `51 passed`
- 为 `tests/conftest.py` 增加项目根路径注入，避免测试运行时 `api` 模块导入失败
- 开始更新 `README.md` 与 `.env.example`，将 PostgreSQL 调整为文档中的正式数据库方案
- 修复前端 `Matching.tsx` 中导出 PDF/Excel 的 `window.open` URL 缺少 `/api` 前缀的 bug
- 新增 `frontend/vitest.config.ts` 用于 vitest 测试配置
- 新增 `frontend/src/__tests__/api-paths.test.ts`（3 个 API 路径一致性测试），vitest 全部通过
- 所有 5 个 Phase 全部完成 ✓
