# GitHub 仓库整理说明

本文档说明最终提交前仓库结构、分支策略和交付物位置，便于评审者快速定位代码、数据库脚本和展示材料。

## 一、分支策略

- 主分支：`main`
- 最终开发提交分支：`lll`
- 当前阶段所有新增代码、数据库脚本、测试脚本和展示文档均提交在 `lll` 分支。
- 不直接向 `main` 推送改动，后续可通过 Pull Request 合并。

远端 PR 地址：

```text
https://github.com/Nianle-Li/fudan-campus-qa-system/pull/new/lll
```

## 二、仓库结构

| 路径 | 内容 |
| :--- | :--- |
| `backend/` | Python 后端服务、API 说明和依赖文件 |
| `frontend/` | 静态前端页面、样式和交互脚本 |
| `db/` | 建表入口、初始化入口、种子数据和 SQL 验收查询 |
| `migrations/` | 按顺序拆分的 PostgreSQL 迁移脚本 |
| `docs/` | 需求、关系模式、约束、阶段演示、最终展示和自测说明 |
| `design/` | ER 图源文件和导出图 |
| `scripts/` | 最终自测辅助脚本 |

## 三、最终交付物索引

- 可运行系统入口：`backend/app.py`、`frontend/index.html`
- 数据库初始化：`db/init.sql`
- 初始测试数据：`db/seeds/001_initial_data.sql`
- 关键 SQL 验收：`db/verify_basic_queries.sql`
- 自动冒烟测试：`scripts/smoke_test.py`
- 阶段演示说明：`docs/阶段演示说明.md`
- 自我测试说明：`docs/自我测试说明.md`
- 最终展示材料：`docs/最终展示材料.md`

## 四、清理结果

- README 已补充最终运行入口和交付材料索引。
- 后端、前端、数据库、脚本目录均有独立 README。
- 数据库脚本分为“迁移脚本”“一键初始化”“种子数据”“验收查询”，避免评审时反复翻找。
- 前端由后端静态托管，演示时只需打开一个地址。
- `.gitignore` 已排除 `.env`、日志、Python 缓存和本地数据库目录，避免提交本地临时文件。
