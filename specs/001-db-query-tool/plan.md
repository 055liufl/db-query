# 实现计划：数据库查询工具

**分支**：`001-db-query-tool` | **日期**：2026-03-29 | **规格**：[spec.md](./spec.md)
**输入**：功能规格说明 `/specs/001-db-query-tool/spec.md`

## 摘要

构建一个面向内部开发/分析人员的数据库查询 Web 工具。用户通过添加 PostgreSQL
或 MySQL 连接 URL，系统自动识别数据库类型并抓取、缓存表/视图元数据，支持直接
编写 SQL 查询（仅 SELECT，自动补充 LIMIT 1000）以及通过自然语言借助 LLM 生成
SQL（自动匹配目标数据库方言）。后端采用 FastAPI + asyncpg/aiomysql + sqlglot +
aiohttp，前端采用 React + Refine 5 + Monaco Editor，通过 Docker 在 Ubuntu 20.04
环境下运行（亦兼容 Win10 + Docker Toolbox）。

## 技术上下文

**语言/版本**：Python 3.12+（后端，通过 `uv` 管理）；TypeScript 5.x（前端）
**主要依赖**：
- 后端：FastAPI、asyncpg（PostgreSQL）、aiomysql（MySQL）、sqlglot（多方言 SQL 解析）、aiohttp（OpenAI 兼容 HTTP）、Pydantic v2
- 前端：React 18、Refine 5、Tailwind CSS、Ant Design 5、Monaco Editor

**存储**：
- SQLite（`~/.db_query/db_query.db`）：存储数据库连接信息与元数据缓存
- 目标数据库：PostgreSQL 或 MySQL（只读查询，不写入；URL scheme 自动识别）

**测试**：pytest + httpx（后端）；无前端测试要求（内部工具）
**目标平台**：Ubuntu 20.04 + Docker（亦兼容 Win10 + Docker Toolbox）；前后端均容器化
**项目类型**：Web 应用（后端 REST API + 前端 SPA）
**性能目标**：
- 连接 + 元数据加载 ≤ 30 秒（首次）；缓存复用时 ≤ 1 秒
- SQL 校验反馈 ≤ 2 秒；查询结果返回 ≤ 10 秒（1000 行内）
- LLM 生成 SQL ≤ 15 秒

**约束**：
- CORS 允许所有 origin
- 无身份认证
- SQL 仅允许 SELECT 语句（sqlglot 校验）
- 无 LIMIT 子句时自动追加 LIMIT 1000
- OPENAI_API_KEY 从环境变量读取

**规模/范围**：内部工具，≤10 名并发用户，单机 Docker 部署

## 宪法检查

*关卡：在 Phase 0 研究之前必须通过。Phase 1 设计完成后重新检查。*

| 原则 | 状态 | 说明 |
|------|------|------|
| 一、后端 Ergonomic Python / 前端 TypeScript | ✅ 通过 | 后端 Python + FastAPI，前端全部使用 TypeScript |
| 二、严格类型标注 | ✅ 通过 | 后端使用 Python 类型提示，前端定义所有 API 响应接口，禁止 `any` |
| 三、Pydantic 数据模型 | ✅ 通过 | 所有请求体/响应体均通过 Pydantic v2 模型定义 |
| 四、后端 JSON 使用 camelCase | ✅ 通过 | 所有 Pydantic 模型配置 `alias_generator=to_camel` |
| 五、无需认证，开放访问 | ✅ 通过 | 无 JWT/Session/OAuth，CORS 允许所有 origin |

**结论**：所有关卡通过，可进入 Phase 0 研究阶段。

## 项目结构

### 文档（本功能）

```text
specs/001-db-query-tool/
├── plan.md              # 本文件
├── research.md          # Phase 0 输出
├── data-model.md        # Phase 1 输出
├── quickstart.md        # Phase 1 输出
├── contracts/           # Phase 1 输出
│   └── api.md
└── tasks.md             # Phase 2 输出（/speckit.tasks 命令生成）
```

### 源码结构（`db-query/` 根目录）

```text
backend/
├── pyproject.toml           # uv 项目配置
├── Dockerfile
├── .env.example
└── app/
    ├── main.py              # FastAPI 应用入口，CORS 配置
    ├── models/
    │   ├── db_connection.py # 数据库连接 Pydantic 模型
    │   ├── metadata.py      # 表/视图元数据 Pydantic 模型
    │   └── query.py         # 查询请求/响应 Pydantic 模型
    ├── services/
    │   ├── connection.py    # 数据库连接管理（PostgreSQL + MySQL URL 检测与连通性测试）
    │   ├── metadata.py      # 元数据抓取与缓存（按 URL scheme 分派 asyncpg / aiomysql）
    │   ├── query.py         # SQL 校验与执行（多方言 sqlglot + 对应驱动）
    │   ├── sql_select.py    # 单条 SELECT 解析（支持 postgres / mysql 方言）
    │   └── llm.py           # aiohttp 集成 OpenAI 兼容接口，自然语言→SQL（自动切换 PG/MySQL 提示词）
    ├── routers/
    │   └── dbs.py           # /api/v1/dbs 路由
    └── storage/
        └── sqlite.py        # SQLite 读写封装（aiosqlite）

frontend/
├── package.json
├── tsconfig.json
├── Dockerfile
├── vite.config.ts
└── src/
    ├── App.tsx
    ├── types/               # 所有 API 响应的 TypeScript 接口
    │   ├── db.ts
    │   └── query.ts
    ├── services/
    │   └── api.ts           # 统一 API 调用封装
    ├── pages/
    │   ├── DatabaseList.tsx # 数据库连接列表页
    │   └── QueryPage.tsx    # SQL 编辑器与查询结果页
    └── components/
        ├── DatabaseForm.tsx # 添加数据库连接表单
        ├── MetadataPanel.tsx# 元数据浏览面板
        ├── SqlEditor.tsx    # Monaco Editor 封装
        ├── NaturalQuery.tsx # 自然语言输入组件
        └── ResultTable.tsx  # 查询结果表格组件

docker-compose.yml           # 统一编排前后端服务
```

**结构决策**：采用前后端分离的 Web 应用结构。所有源码位于工作区根目录
`db-query/` 下，后端在 `db-query/backend/`，前端在 `db-query/frontend/`，
通过 `db-query/docker-compose.yml` 统一编排。

## 复杂度追踪

> 无宪法违规，此表为空。

## 宪法检查（Phase 1 设计后复查）

| 原则 | 状态 | 设计验证点 |
|------|------|-----------|
| 一、后端 Ergonomic Python / 前端 TypeScript | ✅ 通过 | 所有后端文件为 `.py`，前端文件为 `.tsx/.ts` |
| 二、严格类型标注 | ✅ 通过 | `types/` 目录定义所有响应接口；后端模型有完整类型提示 |
| 三、Pydantic 数据模型 | ✅ 通过 | `models/` 目录下所有模型继承 `BaseModel` |
| 四、后端 JSON 使用 camelCase | ✅ 通过 | 全局 `model_config` 配置 `alias_generator=to_camel` |
| 五、无需认证，开放访问 | ✅ 通过 | FastAPI 无认证中间件，CORS `allow_origins=["*"]` |
