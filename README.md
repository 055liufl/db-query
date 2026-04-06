# DB Query

面向 **PostgreSQL** 的只读 Web 查询工具：在浏览器中管理连接、浏览 Schema、编写 **SQL** 或通过 **自然语言** 生成 SQL，并以表格展示结果。连接信息与元数据缓存在本地 **SQLite**；执行查询时直连目标 Postgres（只读）。

典型部署环境：**Windows 10 + Docker Toolbox**（Docker Machine 虚拟机 IP，如 `192.168.99.100`）。

---

## 功能概览

| 能力 | 说明 |
|------|------|
| 连接管理 | 添加 / 编辑 / 删除已保存的 PostgreSQL 连接（DSN 存 SQLite） |
| Schema 浏览 | 拉取并缓存表、视图及列信息；支持刷新元数据 |
| SQL 执行 | Monaco 编辑器；仅允许 **SELECT**（含 **WITH**）；无 `LIMIT` 时自动追加 `LIMIT 1000` |
| 自然语言 SQL | 使用 OpenAI 兼容接口，根据 Schema 生成查询；服务端校验列名与语法 |
| API 文档 | FastAPI 自带 **Swagger UI**（`/docs`） |

---

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python 3.12+、[uv](https://github.com/astral-sh/uv)、FastAPI、asyncpg、sqlglot、aiohttp（OpenAI 兼容 HTTP）、Pydantic v2 |
| 前端 | TypeScript、React 18、Vite、Refine 5、Ant Design 5、Tailwind CSS、Monaco Editor |
| 本地存储 | SQLite（`~/.db_query/db_query.db`，容器内为 `/root/.db_query`） |
| 容器 | docker-compose 3.3（兼容旧版 Docker Toolbox）、PostgreSQL 16（可选示例库） |

---

## 仓库结构

```text
db-query/
├── backend/                 # FastAPI 应用（app/）
├── frontend/                # React + Vite
├── docker-compose.yml       # postgres + backend + frontend
├── docker-compose.test.yml  # 可选：容器内 pytest / Vitest（见下文）
├── docker-troubleshooting.md
├── specs/                   # 需求与说明（非运行时代码）
└── .github/workflows/ci.yml
```

---

## 环境要求

- **Docker**（Docker Toolbox / Docker Desktop 均可；本仓库在 **Docker Toolbox** 下验证）
- 若使用 Docker Machine：虚拟机需能访问外网（拉镜像、OpenAI 等）；前端访问地址一般为 `http://<虚拟机IP>:3000`，API 为 `http://<虚拟机IP>:8000`（前端通过同主机名 + 端口 8000 调用后端）

---

## 快速开始（Docker Compose）

1. **准备后端环境变量**

   复制 `backend/.env.example` 为 `backend/.env`，按需填写：

   | 变量 | 说明 |
   |------|------|
   | `OPENAI_API_KEY` | 自然语言生成 SQL 所需；不填则仅支持手写 SQL |
   | `OPENAI_BASE_URL` | 可选，默认 `https://api.openai.com/v1` |
   | `OPENAI_MODEL` | 可选，默认 `gpt-4o-mini` |

   > **不要在 compose 里把 `backend/.env` 以文件挂载为容器内 `.env`**：若宿主曾误建名为 `.env` 的目录，会挂载成目录导致崩溃。当前 compose 使用 `env_file` 注入即可。

2. **构建并启动**

   ```bash
   docker-compose up --build
   ```

3. **访问**

   - 前端：`http://<Docker Machine IP>:3000`（示例：`http://192.168.99.100:3000`）
   - 后端 API / Swagger：`http://<Docker Machine IP>:8000/docs`

4. **首次使用**

   在左侧「添加连接」保存 PostgreSQL URL（可与 compose 中的 `postgres` 服务同网段，例如 `postgresql://postgres:postgres@postgres:5432/postgres` 从容器内访问；从宿主机浏览器访问时，请按实际主机名与端口填写）。

---

## 本地开发（无 Docker）

```bash
# 后端
cd backend
uv sync --extra dev
uv run uvicorn app.main:app --reload

# 前端（另开终端）
cd frontend
npm install
npm run dev
```

默认 API：`http://127.0.0.1:8000`；前端可设置 `VITE_API_BASE_URL` 指向后端。

---

## 测试与 CI

| 类型 | 命令 |
|------|------|
| 后端 | `cd backend && uv run ruff check app tests && uv run mypy && uv run pytest` |
| 集成测试 | 设置 `POSTGRES_INTEGRATION_URL` 后运行 pytest（见 `tests/test_integration_postgres.py`） |
| 前端 | `cd frontend && npm test`（Vitest） |

GitHub Actions（`.github/workflows/ci.yml`）：后端 Ruff + Mypy + Pytest（带 Postgres 服务），前端 `npm install && npm test`。

---

## 可选：Compose 内跑测试

不随 `docker-compose up` 启动，需显式合并文件：

```bash
docker-compose -f docker-compose.yml -f docker-compose.test.yml run --rm backend-test
docker-compose -f docker-compose.yml -f docker-compose.test.yml run --rm frontend-test
```

（`backend-test` 使用 `backend/Dockerfile.test`，含开发依赖与 `tests/`。）

---

## HTTP API 摘要

前缀：`/api/v1`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/dbs` | 列出已保存连接 |
| PUT | `/dbs/{name}` | 创建或更新连接 |
| DELETE | `/dbs/{name}` | 删除连接 |
| GET | `/dbs/{name}` | 获取元数据（可 `?refresh=true` 刷新） |
| POST | `/dbs/{name}/query` | 执行只读 SQL |
| POST | `/dbs/{name}/query/natural` | 自然语言生成 SQL（仅返回 `generatedSql`，不自动执行） |
| GET | `/api/v1/health` | 健康检查（含 LLM 传输层标识） |

JSON 响应字段使用 **camelCase**。

---

## SQL 安全策略

- 使用 **sqlglot**（`dialect="postgres"`）解析，仅允许单条 **SELECT** / **WITH … SELECT**。
- 禁止 DML/DDL；未带 `LIMIT` 时自动追加 `LIMIT 1000`（自然语言生成路径在校验阶段不追加，执行时与手写 SQL 一致）。

---

## Docker 与 Docker Toolbox

Compose **3.3**、构建与运行、网络与 API、LLM、VirtualBox 资源、Codex CLI 与密钥约定、容器内测试等：**见 [`docker-troubleshooting.md`](./docker-troubleshooting.md)**（单一事实来源）。

---

## 常见问题（摘要）

更细步骤与命令仍以 **`docker-troubleshooting.md`** 为准。

- **前端能打开但 API 失败**：勿混用 VM IP 与 `localhost`；见排障文档 **§7**。
- **自然语言报错**：`OPENAI_API_KEY` / `OPENAI_BASE_URL`；见 **§5、§10**。
- **列名不存在**：刷新元数据或 `SELECT *`；见 **§10.4**。

---

## 许可证

若未在仓库中另行声明，默认以项目课程 / 组织要求为准；使用第三方依赖时请遵守其许可证。
