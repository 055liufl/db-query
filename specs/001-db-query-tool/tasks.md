---
description: "数据库查询工具任务清单"
---

# 任务清单：数据库查询工具

**输入**：`specs/001-db-query-tool/` 下的 plan.md、spec.md、data-model.md、contracts/api.md
**前置条件**：plan.md（必须）、spec.md（必须）

## 格式：`[ID] [P?] [US?] 描述`

- **[P]**：可并行执行（不同文件，无依赖）
- **[US1/2/3]**：对应用户故事编号

---

## Phase 1：基础设施与后端核心（US1 + US2）

**目标**：完成项目初始化、后端全部功能（连接管理、元数据、SQL 查询），可通过 API 独立验证。

### 项目初始化

- [x] T001 [P] 初始化后端项目：`backend/pyproject.toml`（uv，FastAPI、asyncpg、sqlglot、openai、aiosqlite 依赖）、`backend/Dockerfile`、`backend/.env.example`
- [x] T002 [P] 初始化前端项目：`frontend/package.json`（React 18、Refine 5、Tailwind、Ant Design 5、Monaco Editor、Vite）、`frontend/tsconfig.json`、`frontend/Dockerfile`
- [x] T003 [P] 创建 `docker-compose.yml`，编排 backend（8000）和 frontend（3000）服务，挂载 SQLite volume

### 后端基础层

- [x] T004 [P] [US1] 创建公共基类 `backend/app/models/__init__.py`（`AppBaseModel`，配置 `alias_generator=to_camel`）
- [x] T005 [P] [US1] 创建 SQLite 存储封装 `backend/app/storage/sqlite.py`（aiosqlite，建表 `db_connections`、`db_metadata`，提供 CRUD 接口）
- [x] T006 [P] [US1] 创建 FastAPI 入口 `backend/app/main.py`（CORS `allow_origins=["*"]`，注册路由，lifespan 初始化 SQLite）

### 后端 US1：数据库连接与元数据

- [x] T007 [P] [US1] 创建连接模型 `backend/app/models/db_connection.py`（`DbConnectionCreate`、`DbConnectionResponse`，含 camelCase 别名）
- [x] T008 [P] [US1] 创建元数据模型 `backend/app/models/metadata.py`（`ColumnInfo`、`TableInfo`、`DbMetadataResponse`）
- [x] T009 [US1] 实现连接服务 `backend/app/services/connection.py`（asyncpg 连通性测试，URL 格式校验）
- [x] T010 [US1] 实现元数据服务 `backend/app/services/metadata.py`（查询 `information_schema`，结果序列化为 JSON，写入/读取 SQLite 缓存；支持 `?refresh=true`）
- [x] T011 [US1] 实现路由 `backend/app/routers/dbs.py`：`GET /api/v1/dbs`、`PUT /api/v1/dbs/{name}`、`GET /api/v1/dbs/{name}`

### 后端 US2：SQL 查询

- [x] T012 [P] [US2] 创建查询模型 `backend/app/models/query.py`（`QueryRequest`、`QueryResult`、`ErrorResponse`）
- [x] T013 [US2] 实现查询服务 `backend/app/services/query.py`（sqlglot 校验：单条 SELECT only；无 LIMIT 自动追加 LIMIT 1000；asyncpg 执行并返回结果）
- [x] T014 [US2] 在 `backend/app/routers/dbs.py` 中追加 `POST /api/v1/dbs/{name}/query`

**Phase 1 检查点**：`docker-compose up --build` 后，通过 Swagger（`/docs`）可完成：添加连接→获取元数据→执行 SELECT 查询，全链路验证通过。

---

## Phase 2：前端界面（US1 + US2）

**目标**：实现完整的前端 UI，用户可通过浏览器完成 P1、P2 用户故事的全流程操作。

**前置**：Phase 1 完成

### 前端类型与 API 层

- [x] T015 [P] [US1] 定义 TypeScript 接口 `frontend/src/types/db.ts`（`DbConnection`、`DbMetadata`、`TableInfo`、`ColumnInfo`）
- [x] T016 [P] [US2] 定义 TypeScript 接口 `frontend/src/types/query.ts`（`QueryRequest`、`QueryResult`、`QueryColumn`）
- [x] T017 [US1] 实现 API 封装 `frontend/src/services/api.ts`（所有端点调用，统一错误处理，读取 `VITE_API_BASE_URL`）

### 前端 US1：连接管理与元数据展示

- [x] T018 [P] [US1] 实现 `frontend/src/components/DatabaseForm.tsx`（添加连接表单：名称 + URL 输入，校验，提交，错误展示）
- [x] T019 [P] [US1] 实现 `frontend/src/components/MetadataPanel.tsx`（左侧面板：表/视图列表，展开显示字段名+类型，支持搜索过滤）
- [x] T020 [US1] 实现 `frontend/src/pages/DatabaseList.tsx`（连接列表页：展示所有连接，点击连接进入查询页，使用 Refine 数据钩子）

### 前端 US2：SQL 编辑器与查询结果

- [x] T021 [P] [US2] 实现 `frontend/src/components/SqlEditor.tsx`（Monaco Editor 封装：PostgreSQL 语法高亮，受控模式，支持外部值写入）
- [x] T022 [P] [US2] 实现 `frontend/src/components/ResultTable.tsx`（Ant Design Table：动态列，空状态提示，LIMIT 截断提示，加载状态）
- [x] T023 [US2] 实现 `frontend/src/pages/QueryPage.tsx`（查询页主体：左侧 MetadataPanel + 右侧 SqlEditor + ResultTable，错误信息展示）
- [x] T024 [US1/2] 实现 `frontend/src/App.tsx`（路由配置：`/` → DatabaseList，`/query/:name` → QueryPage）

**Phase 2 检查点**：打开浏览器，可完整体验：添加连接→浏览元数据→编辑 SQL→执行查询→查看结果表格，所有错误场景有中文提示。

---

## Phase 3：自然语言生成 SQL（US3）

**目标**：在 Phase 2 基础上叠加 LLM 自然语言生成 SQL 功能。

**前置**：Phase 1、Phase 2 完成

### 后端 US3

- [x] T025 [P] [US3] 创建自然查询模型：在 `backend/app/models/query.py` 中追加 `NaturalQueryRequest`、`NaturalQueryResult`
- [x] T026 [US3] 实现 LLM 服务 `backend/app/services/llm.py`（openai SDK v1.x，从 SQLite 读取元数据作为 system prompt，超时 30s，异常返回友好错误）
- [x] T027 [US3] 在 `backend/app/routers/dbs.py` 中追加 `POST /api/v1/dbs/{name}/query/natural`

### 前端 US3

- [x] T028 [P] [US3] 定义 TypeScript 接口：在 `frontend/src/types/query.ts` 中追加 `NaturalQueryRequest`、`NaturalQueryResult`
- [x] T029 [P] [US3] 实现 `frontend/src/components/NaturalQuery.tsx`（自然语言输入框 + "生成 SQL" 按钮，加载状态，错误提示）
- [x] T030 [US3] 在 `frontend/src/pages/WorkspacePage.tsx` 中集成 `NaturalQuery` 组件：生成的 SQL 自动填入 `SqlEditor`，不自动执行（原 QueryPage 已合并为工作台）

**Phase 3 检查点**：输入自然语言描述 → 点击"生成 SQL" → SQL 出现在编辑器 → 用户点击"执行"→ 结果展示。LLM 不可用时有中文错误提示且不影响手动 SQL 功能。

---

## Phase 4：迁移、测试与收尾（`specs/instructions.md`）

**目标**：SQLite 可版本化迁移、后端 pytest、REST 契约用例补全、Playwright 冒烟；项目可重复验证。

### 数据库迁移

- [x] T031 [P] 实现 SQLite 迁移链：`backend/app/storage/migrate.py`（`schema_migrations` + 版本化 DDL），`init_db()` 仅通过迁移落库

### 后端测试

- [x] T032 [P] 添加 `backend/tests/`：`conftest.py`（`TestClient` + 临时 `DB_QUERY_PATH`）、连接校验、`validate_and_prepare_sql`、迁移幂等、API 无外部 PG 的用例

### 契约与 E2E

- [x] T033 [P] 更新 `fixtures/test.rest`（含 `DELETE /api/v1/dbs/{name}`）
- [x] T034 [P] 前端 `playwright.config.ts` + `e2e/smoke.spec.ts`，`npm run test:e2e`

**Phase 4 检查点**：`cd backend && uv sync --extra dev && uv run pytest` 全绿；`cd frontend && npm run test:e2e`（自动起 dev server）通过。

---

## Phase 5：MySQL 支持（多数据库扩展）

**目标**：在已有 PostgreSQL 支持基础上，新增 MySQL 连接、元数据提取、查询执行和自然语言 SQL 生成支持。系统根据连接 URL scheme 自动识别数据库类型。

**前置**：Phase 1–4 完成

### 后端 MySQL 支持

- [x] T035 [P] 在 `pyproject.toml` 中添加 `aiomysql>=0.2.0` 依赖
- [x] T036 [P] 扩展 `connection.py`：新增 `detect_db_type()`、`validate_db_url()`、`_parse_mysql_url()`、`test_mysql_connection()`、`test_connection()` 统一分派
- [x] T037 更新 `sql_select.py`：`parse_single_select_statement()` 接受 `dialect` 参数，支持 `"postgres"` 和 `"mysql"`
- [x] T038 扩展 `metadata.py`：新增 `fetch_metadata_from_mysql()`（查询 MySQL `information_schema`，过滤系统 schema）；新增 `fetch_metadata()` 统一分派
- [x] T039 扩展 `query.py`：新增 `_execute_select_mysql()`（aiomysql + DictCursor + MySQL 类型映射）；`validate_and_prepare_sql()` 接受 `dialect` 参数；`execute_select()` 统一分派
- [x] T040 更新 `llm.py`：`generate_select_sql()` 根据连接 URL 检测数据库类型，system prompt 动态切换 PostgreSQL/MySQL 专家角色和语法要求；列校验 `_validate_llm_columns_against_metadata()` 支持无显式 schema 匹配（MySQL 默认 schema 为数据库名）
- [x] T041 更新 `routers/dbs.py`：`put_db` 使用 `validate_db_url()` + `test_connection()` 统一入口；`get_db_metadata` 使用 `fetch_metadata()` 分派；异常处理兼容 aiomysql 错误

### 前端与配置

- [x] T042 [P] 更新 `DatabaseForm.tsx` placeholder 提示支持 MySQL URL 格式
- [x] T043 [P] 更新 `docker-compose.yml`：backend 服务增加 `extra_hosts: host.docker.internal:host-gateway`，使容器内可访问宿主机 MySQL

### 测试

- [x] T044 [P] 更新 `tests/test_connection.py`：新增 MySQL URL 检测、解析、校验用例
- [x] T045 [P] 更新 `tests/test_sql_select.py`：新增 MySQL 方言解析用例
- [x] T046 [P] 新增 `tests/test_integration_mysql.py`：MySQL 连接、元数据、查询集成测试（需设置 `MYSQL_INTEGRATION_URL`）

**Phase 5 检查点**：使用 `mysql://root@host.docker.internal:3306/todo_db` 添加连接 → 浏览元数据 → 执行 `SELECT * FROM todos` → 自然语言生成 MySQL SQL，全链路验证通过。

---

## 依赖与执行顺序

```
Phase 1（后端）
  T001-T003（初始化）→ T004-T006（基础层）→ T007-T014（业务逻辑）

Phase 2（前端）— 依赖 Phase 1 完成
  T015-T017（类型+API层）→ T018-T022（组件）→ T023-T024（页面组合）

Phase 3（US3）— 依赖 Phase 1 + Phase 2 完成
  T025-T027（后端）‖ T028-T029（前端组件）→ T030（页面集成）

Phase 4（迁移/测试）— 依赖 Phase 1–3
  T031 ‖ T032 ‖ T033 ‖ T034

Phase 5（MySQL 支持）— 依赖 Phase 1–4
  T035-T037（依赖+解析层）→ T038-T041（业务服务）‖ T042-T043（前端+配置）→ T044-T046（测试）
```

### 并行机会

- Phase 1 中：T001、T002、T003、T004、T005、T006 均可并行启动
- Phase 1 中：T007、T008、T012 可与 T009、T010 并行
- Phase 2 中：T015、T016 可与 T017 并行；T018-T022 均可并行
- Phase 3 中：T025-T027（后端）与 T028-T029（前端）可并行
- Phase 4 中：T031–T034 均可并行
- Phase 5 中：T035-T037 可并行；T038-T041 与 T042-T043 可并行；T044-T046 可并行
