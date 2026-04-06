# Docker 排障与约定（db-query）

本文件为 **Docker / Compose / 浏览器 / 自然语言 SQL** 的单一事实来源，与 `docker-compose.yml`、`docker-compose.test.yml`、`backend/Dockerfile`、`backend/Dockerfile.test`、`frontend/Dockerfile` 及后端当前实现一致。

---

## 1. 快速开始（Compose）

1. `cp backend/.env.example backend/.env`，填写 `OPENAI_API_KEY`（自然语言 SQL 需要；可选 `OPENAI_BASE_URL`、`OPENAI_MODEL`）。
2. 仓库根目录执行：`docker-compose up --build`。
3. 浏览器访问（Docker Toolbox 用虚拟机 IP，勿用 `localhost` 代替 VM）：
   - 前端：`http://<docker-machine-ip>:3000`
   - API / Swagger：`http://<docker-machine-ip>:8000/docs`  
   获取 IP：`docker-machine ip default`（示例：`192.168.99.100`）。
4. 修改 `.env` 后：`docker-compose up -d --force-recreate backend`。

**Compose 约定**：`backend` 使用 `env_file: ./backend/.env` 注入环境变量；**不要** bind-mount `./backend/.env` → `/app/.env`（宿主机若曾误建名为 `.env` 的目录，会挂载成目录导致崩溃）。**不要**用 `environment: OPENAI_*: ${...}` 空串覆盖 `env_file`。

---

## 2. 旧版 `docker-compose` 与 YAML

| 问题 | 处理 |
|------|------|
| `UnicodeDecodeError: 'gbk' codec can't decode` | `docker-compose.yml` 须 **UTF-8**，注释**仅 ASCII**（勿中文、弯引号、长破折号）；或改用 **Compose V2**（`docker compose`） |
| `Version ... is unsupported` 或仅支持 2.x/3.3 | 本仓库使用 **`version: "3.3"`** 以兼容旧版 Docker Toolbox；勿用 3.9+（会报错） |
| `${VAR:-}` / invalid interpolation | 本仓库已避免；密钥用 **`env_file`** |

---

## 3. 构建常见错误（镜像）

### 3.1 `pip` / DNS / 超时

| 现象 | 处理 |
|------|------|
| `Temporary failure in name resolution` | 在 VM 内修 DNS（见 `docker-compose.yml` 顶部注释），再 `docker-compose build --no-cache backend` |
| `RuntimeError: can't start new thread`（pip/Rich） | `Dockerfile` 已设 `PIP_PROGRESS_BAR=off`；仍失败见 **§9** 加大 VM |
| `ReadTimeoutError` / PyPI | 已加长 `PIP_DEFAULT_TIMEOUT` 与 `--retries`；可用 `build-arg` 国内镜像（见 `docker-compose.yml` 注释） |
| `uv` / Tokio `PermissionDenied` | 镜像内使用 **pip**（非 uv）；本机开发可用 **`uv run`** |

### 3.2 多阶段 `backend`：`test` 阶段 `pip install ".[dev]"` 失败

**现象**：`index url "" seems invalid`、`Could not find hatchling`。

**原因**：`ARG PIP_INDEX_URL` 在 `FROM base AS test` 新阶段**不继承**，展开为空。

**处理**：已在 `backend/Dockerfile` 的 `test` 阶段重新声明 `ARG PIP_INDEX_URL` / `ARG PIP_TRUSTED_HOST`（见该文件）。若自建镜像，请保持与 `base` 阶段一致。

### 3.3 前端：`npm ci` 失败

**处理**：`frontend/Dockerfile` 使用 `package-lock.json` + `npm ci`；需保证 lockfile 与 `package.json` 一并提交。

---

## 4. 可选：容器内测试（`docker-compose.test.yml`）

默认 **`docker-compose up`** 不启动测试服务。需显式合并文件（且依赖已起的 `postgres` 等同网络）：

```bash
docker-compose -f docker-compose.yml -f docker-compose.test.yml run --rm backend-test
docker-compose -f docker-compose.yml -f docker-compose.test.yml run --rm frontend-test
```

- `backend-test`：使用 `backend/Dockerfile.test`（含 dev 依赖与 `tests/`）。  
- `frontend-test`：同一前端镜像，命令为 `npm test`。

---

## 5. 环境变量（`backend/.env`）

| 变量 | 说明 |
|------|------|
| `OPENAI_API_KEY` | 自然语言 SQL 需要；不配则仅手写 SQL |
| `OPENAI_BASE_URL` | 可选；默认 `https://api.openai.com/v1`。须为 OpenAI 兼容网关的 `.../v1`；仅 `api.openai.com` 无路径时后端会补 `/v1` |
| `OPENAI_MODEL` | 可选；默认 `gpt-4o-mini`（须与上游允许列表一致） |
| `DB_QUERY_PATH` | 可选；SQLite 数据目录（容器内常用 `/root/.db_query`） |

**自检（勿泄露完整 key）**：

```bash
docker exec <backend容器名> python -c "from app.core.config import get_settings; s=get_settings(); print('has_key:', bool(s.openai_api_key), 'model:', s.openai_model)"
```

容器名以 `docker ps` 为准（文档中 `dbquery_backend_1` 仅为示例）。

**Git Bash** 路径被改写：`//` 前缀或 `export MSYS_NO_PATHCONV=1`。

---

## 6. PostgreSQL 与连接串

单独起库：`docker-compose up -d postgres`；`docker ps` 应见 `0.0.0.0:5432->5432/tcp`。

| 场景 | 连接串中的 host |
|------|-----------------|
| Docker Desktop（本机） | `127.0.0.1` |
| Docker Toolbox | **`docker-machine ip default`**（在浏览器里填的 URL 用该 IP） |

- **Backend 容器内**保存的 DSN：应指向服务名 **`postgres`**，例如 `postgresql://postgres:postgres@postgres:5432/postgres`。容器内 **`127.0.0.1` / `localhost`** 指向 backend 自身，不是 compose 里的 Postgres。
- `POST .../query` 返回 500：看 JSON 的 `message` / `detail`；纯文本时 `docker logs <backend容器>`。

---

## 7. 浏览器与 API（含 Failed to fetch）

- Toolbox：访问 **`http://<docker-machine-ip>:3000`** 与 **`:8000`**，勿把 **`localhost`** 当成 VM 上的服务地址。
- 未设置 **`VITE_API_BASE_URL`** 时，前端请求 **`当前页面主机名:8000`**；页面用 VM IP 却写死 `localhost:8000` 会 **Failed to fetch**。
- 确认 **`http://<与页面同主机>:8000/docs`** 可打开。后端已 **CORS** 与 **Private Network Access** 头。

**若希望用本机 `localhost` 访问 Toolbox 端口**：在 VirtualBox 的 `default` 虚拟机配置端口转发（如 8000→8000、3000→3000），或统一使用 `docker-machine ip`。

---

## 8. `http://<IP>:8000` 无法打开 / `ERR_CONNECTION_REFUSED`

1. `docker ps -a`：backend 是否 **Up**，是否映射 `0.0.0.0:8000->8000/tcp`。  
2. **Exited**：`docker logs <backend容器>`。  
3. 端口冲突：改 `docker-compose.yml` 的 `ports`，并同步前端或 `VITE_API_BASE_URL`。

---

## 9. Backend 容器启动失败（线程 / 依赖）

先查：`docker logs <backend容器>`。

| 原因 | 处理 |
|------|------|
| **uvloop / httptools** | `Dockerfile` 使用 `uvicorn ... --loop asyncio --http h11` |
| SQLite `can't start new thread` | 存储层使用标准库 **`sqlite3`**（无 aiosqlite 额外线程） |
| 自然语言 / aiohttp `can't start new thread` | 见 **§10**；仍失败则 **§11** 加大 VM |

---

## 10. 自然语言生成 SQL（LLM）

### 10.1 响应 `error` 含义

| `error` | 含义 |
|---------|------|
| `llm_unavailable` | 无密钥、网络/上游 API 失败；`detail` 为摘要（不含密钥） |
| `natural_query_unusable` | 模型输出无法通过校验（如非单条 SELECT、列名不在元数据等）；**400** |
| `internal_error` / 其它 | 未捕获异常；看 `detail` |

### 10.2 实现要点（与排障相关）

- HTTP：`aiohttp` 调 `{OPENAI_BASE_URL}/chat/completions`。
- DNS：同步 `socket.getaddrinfo`（避免 aiodns/pycares 额外线程，适配 **Toolbox 低 nproc**）。
- 官方域名无 `/v1` 时会纠正为 `https://api.openai.com/v1`。
- Compose：`shm_size` / `ulimits.nofile` 见 `docker-compose.yml`。

### 10.3 自检

```bash
curl -sS "http://127.0.0.1:8000/api/v1/health"
```

应含 `"llmTransport":"aiohttp"`、`"llmDns":"socket_sync"`。不对则重建镜像：

```bash
docker-compose build --no-cache backend
docker-compose up -d --force-recreate backend
```

### 10.4 按现象排查

| 现象 | 处理 |
|------|------|
| `JSONDecodeError` / 空体 / HTML | `OPENAI_BASE_URL` 须指向 API 而非网页；`curl` 看 Content-Type |
| `HTTP 403` / `model_not_allowed` | 改 `OPENAI_MODEL` 与上游一致，`force-recreate backend` |
| `HTTP 400` / 网关 `openai_error` | 核对密钥、额度、网关日志 |
| **列不存在（执行后报错）** | 界面「刷新元数据」；自然语言优先 **`SELECT *`**，避免模型臆造列名 |

### 10.5 与本机 Codex CLI 的密钥（独立）

| 用途 | 说明 |
|------|------|
| **Codex CLI**（若安装） | 本机终端写代码、跑命令。 |
| **应用内自然语言 SQL** | 仅由 **`OPENAI_API_KEY`**（与 `backend/.env` / compose `env_file`）注入。 |

两者独立；不必在镜像内安装 Codex。

**本机临时 `uv run`（非 Docker）**：

```powershell
$env:OPENAI_API_KEY="sk-..."
cd backend; uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

---

## 11. Docker Toolbox：VirtualBox 资源

Toolbox 的 Linux 在 VirtualBox（多为 `default`）。内存/CPU 过小易出现线程/构建问题。

1. `docker-machine stop default`
2. VirtualBox → 选中 `default` → **设置 → 系统**：内存（如 4096～8192 MB）、处理器（如 4 核）
3. `docker-machine start default`

**PowerShell 示例**（先 `docker-machine stop default`）：

```powershell
& "$env:ProgramFiles\Oracle\VirtualBox\VBoxManage.exe" modifyvm default --memory 8192 --cpus 4
```

**Docker Desktop（WSL2）** 用户在 Desktop **Settings → Resources** 调整，勿用本节 VirtualBox 步骤。

---

## 12. `fixtures/seed.sql`

```bash
docker exec -i <postgres容器名> psql -U postgres -d postgres -v ON_ERROR_STOP=1 < fixtures/seed.sql
```

容器名以 `docker ps` 为准。

---

## 13. CI 与本地测试（摘要）

| 场景 | 命令 |
|------|------|
| 后端 | `cd backend && uv sync --extra dev && uv run ruff check app tests && uv run mypy && uv run pytest` |
| 集成测试 | 设置 `POSTGRES_INTEGRATION_URL` 后运行 pytest |
| 前端 | `cd frontend && npm install && npm test` |

详见仓库根目录 **`README.md`** 与 **`.github/workflows/ci.yml`**。

---

## 14. 不在容器内构建时

```bash
cd backend && uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
cd frontend && npm run dev
```

默认 API：`http://127.0.0.1:8000`；前端可设 `VITE_API_BASE_URL`。
