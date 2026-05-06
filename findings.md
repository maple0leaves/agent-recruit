# Findings

## 2026-05-06

- 当前项目已有完整前后端雏形：`frontend/src/App.tsx` 提供登录、仪表盘、JD、候选人、匹配页面；`api/server.py` 暴露 `/api/...` 前缀的核心接口。
- 后端测试目录已存在：`tests/test_auth.py`、`tests/test_jd.py`、`tests/test_candidate.py`、`tests/test_sse.py`。
- 现有测试文件大量仍使用旧路径，如 `/auth/login`、`/jd`、`/candidates`、`/skills`，而真实后端接口挂载在 `/api` 前缀下。
- 这是一个高优先级、小改动、高收益的问题：修复后能够快速验证“后端接口闭环”这一核心目标。
- 在 `hellojobs` conda 环境中运行关键后端测试后，`tests/test_auth.py`、`tests/test_jd.py`、`tests/test_candidate.py`、`tests/test_sse.py` 共 `51` 个用例已全部通过。
- `README.md` 原先默认仍以 SQLite 说明为主，已开始收口为 PostgreSQL 优先的最小启动路径。
