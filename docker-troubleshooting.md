# Docker 排障与约定（db-query）

本文件为 **Docker / Compose / 浏览器 / 自然语言 SQL** 的**单一事实来源**，与 **`docker-compose.yml`**、**`backend/Dockerfile`**、**`backend/app/core/config.py`**、**`app/services/llm.py`**、**`app/main.py`** 当前实现一致。

---

## 1. 旧版 `docker-compose` 与 YAML

| 问题 | 处理 |
|------|------|
| `UnicodeDecodeError: 'gbk' codec can't decode` | **`docker-compose.yml` 须 UTF-8，注释仅 ASCII**（勿中文、弯引号、长破折号 `—` 等）；或改用 **Compose V2**（`docker compose`） |
| `${VAR:-}` / invalid interpolation | 本仓库已避免；密钥用 **`env_file`** |
| 版本 | **`version: "3.3"`** 兼容 Toolbox |

---

## 2. 环境变量（`backend/.env`）

| 变量 | 说明 |
|------|------|
| **`OPENAI_API_KEY`** | 必填（自然语言 SQL）；不配则只能手写 SQL |
| **`OPENAI_BASE_URL`** | 可选；不配则默认 **`https://api.openai.com/v1`**。须为 OpenAI 兼容网关的 **`.../v1`** 前缀；仅域名无路径时官方 **`api.openai.com`** 会在后端自动补 **`/v1`** |
| **`OPENAI_MODEL`** | 可选；默认 **`gpt-4o-mini`**。第三方网关常限制模型，须与其文档/控制台一致 |
| **`DB_QUERY_PATH`** | 可选；SQLite 数据目录 |

**Compose**：**`env_file: ./backend/.env`** 在启动时注入进程环境；**不** bind-mount **`./backend/.env` → `/app/.env`**，避免宿主机曾误建 **`.env` 目录`** 导致挂载为目录、密钥读不到。Pydantic **`Settings`** 读环境变量（与本地读 **`backend/.env` 文件**等价）。

首次：`cp backend/.env.example backend/.env` 并填写。修改后 **`docker-compose up -d --force-recreate backend`**。

**勿**在 Compose 里用 **`environment: OPENAI_*: ${...}`** 空串覆盖 **`env_file`**。

**自检（勿泄露完整 key）**：

```bash
docker exec dbquery_backend_1 python -c "from app.core.config import get_settings; s=get_settings(); print('has_key:', bool(s.openai_api_key), 'model:', s.openai_model)"
```

**Git Bash** 路径被改写时：**`//`** 前缀或 **`export MSYS_NO_PATHCONV=1`**。

---

## 3. 构建 `backend` 镜像（`RUN pip install .`）

| 现象 | 处理 |
|------|------|
| `Temporary failure in name resolution` | VM 内修 DNS（见 **`docker-compose.yml` 注释**），再 **`docker-compose build --no-cache backend`** |
| **`RuntimeError: can't start new thread`**（pip/Rich） | **`Dockerfile`** 已 **`PIP_PROGRESS_BAR=off`**；仍失败则 **§9.1** 加大 VM 或本机 **`uv run`** |
| `ReadTimeoutError` / PyPI | 已加长 **`PIP_DEFAULT_TIMEOUT`**、**`--retries`**；**`docker-compose.yml`** 注释含镜像 **`build-arg`** |
| **`uv` / Tokio `PermissionDenied`** | 镜像用 **pip**；本机可用 **`uv run`** |
| 不在容器里构建 | `cd backend && uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000` |

---

## 4. PostgreSQL 与连接串

**单独起库**：`docker-compose up -d postgres`。**`docker ps`** 见 **`0.0.0.0:5432->5432/tcp`**。

| 环境 | 连接串 host |
|------|----------------|
| Docker Desktop | `127.0.0.1` |
| Docker Toolbox | **`docker-machine ip default`** |

Backend **容器内**保存的 URL：**host 须为服务名 `postgres`**（如 **`postgresql://postgres:postgres@postgres:5432/postgres`**）。**`127.0.0.1` / `localhost`** 在容器内指向 backend 自身。

**`POST .../query` 500**：看 JSON **`message` / `detail`**；纯文本 500 时 **`docker logs dbquery_backend_1`**。

---

## 5. 浏览器与 API（含 Failed to fetch）

Toolbox：**`http://<docker-machine-ip>:3000`** 与 **`:8000`**，勿用 **`localhost`** 当成 VM 上的 API。

**`api.ts`**：未设 **`VITE_API_BASE_URL`** 时请求 **`当前页面主机:8000`**。页面用 VM IP 却写死 **`localhost:8000`** 会 **Failed to fetch**。自定义基址需 **`VITE_API_BASE_URL`** 并**重建前端**。

确认 **`http://<与页面同主机>:8000/docs`** 可打开。后端已 **CORS** 与 **Private Network Access** 头。

---

## 6. `http://<IP>:8000` 无法打开 / `ERR_CONNECTION_REFUSED`

1. **`docker ps -a`**：**`dbquery_backend_1`** 是否 **Up**，**`0.0.0.0:8000->8000/tcp`**。  
2. **Exited**：**`docker logs dbquery_backend_1`**。  
3. **端口冲突**：改 **`docker-compose.yml`** 的 **`ports`**，并与 **`VITE_API_BASE_URL`** 一致。

---

## 7. `dbquery_backend_1` 启动失败

**先查**：**`docker logs dbquery_backend_1`**。

| 原因 | 处理 |
|------|------|
| **uvloop / httptools** | **`Dockerfile`**：**`uvicorn ... --loop asyncio --http h11`** |
| **`can't start new thread`**（SQLite） | 已用标准库 **`sqlite3`**（无 **`aiosqlite`**） |
| **`can't start new thread`**（自然语言） | **§8** |
| 其它 | **§8**、**§9.1** |

---

## 8. 自然语言生成 SQL（LLM）

### 8.1 响应 `error` 含义

| `error` | 含义 |
|---------|------|
| **`llm_unavailable`** | 无密钥、网络/上游 API 失败；**`detail`** 为摘要（**不含密钥**） |
| **`natural_query_unusable`** | 模型输出无法解析为合法单条 **SELECT**（**400**） |
| **`internal_error`** | 未捕获异常；**`detail`** 含类型与信息 |

### 8.2 后端实现（与排障相关）

- **HTTP**：**`aiohttp.ClientSession`** 请求 **`{OPENAI_BASE_URL}/chat/completions`**（OpenAI 兼容 JSON）。
- **DNS**：自定义 **`AbstractResolver`**，在 **`resolve()`** 内**同步** **`socket.getaddrinfo`**（**不**用 **`asyncio` 默认线程池**、**不**用 **`aiodns`/`pycares`**——后者会引入额外线程，在 **Toolbox 小 VM / 低 nproc** 下易 **`RuntimeError: can't start new thread`**）。DNS 会短暂阻塞事件循环，可接受。
- **官方域名**：若配置为 **`https://api.openai.com`** 或 **`http://api.openai.com`**（无 **`/v1`**），会**自动纠正**为 **`https://api.openai.com/v1`**。
- **Compose**：**`shm_size` / `ulimits.nofile`** 见 **`docker-compose.yml`**；**`main.py`** 未处理异常返回 **JSON**。

### 8.3 部署后自检

```bash
curl -sS "http://127.0.0.1:8000/api/v1/health"
```

应含 **`"llmTransport":"aiohttp"`**、**`"llmDns":"socket_sync"`**。若缺失或不对，说明**旧镜像**，需：

```bash
docker-compose build --no-cache backend
docker-compose up -d --force-recreate backend
```

### 8.4 按现象排查

| 现象 | 原因与处理 |
|------|------------|
| **`can't start new thread`** | 先 **8.3** 确认新镜像；仍失败则 **§9.1** 加大 VM 内存/CPU；本机 **`uv run`** 对比 |
| **`JSONDecodeError` / 空体 / 响应为 HTML** | 请求打到了**网页**而非 API。核对 **`OPENAI_BASE_URL`** 为 **`https://.../v1`**；镜像站须与密钥**同一服务商**。容器内 **`curl`** 看 **Content-Type** 与正文是否 **`{`** 开头 |
| **`HTTP 403` / `model_not_allowed`** | 默认 **`gpt-4o-mini`** 不被上游允许。在 **`backend/.env`** 设 **`OPENAI_MODEL`**（与上游返回列表一致），**`force-recreate backend`** |
| **`HTTP 400` / `bad_response_status_code` / `openai_error`** | **第三方网关**转发上游失败（密钥、额度、地区/网络、上游故障）。在**网关控制台**查日志/额度；本应用仅发标准 **`/v1/chat/completions`** |
| **`detail` 已解析为结构化中文** | 上游 **HTTP ≥400** 时，`detail` 会解析 **`error.type` / `error.message`** 并附简短提示 |

**通用**：**`docker logs dbquery_backend_1`**；**`OPENAI_BASE_URL`** 须在容器内可解析、可访问。

---

## 9. Docker Toolbox：VirtualBox 与 Codex

### 9.1 增大 VirtualBox / Docker Machine 资源

Toolbox 的 Linux 在 **VirtualBox**（多为 **`default`**）。内存/CPU 过小易出现 **线程/构建** 问题。修改后 **`docker-machine start default`** 再 **`docker-compose up`**。

**图形界面（推荐）**

1. **`docker-machine stop default`**
2. **VirtualBox** → 选中 **`default`**
3. **设置 → 系统 → 主板**：内存例如 **4096～8192 MB**
4. **设置 → 系统 → 处理器**：例如 **4** 核
5. **`docker-machine start default`**

**命令行**（先 **`docker-machine stop default`**）。**勿在 Git Bash 用** **`%ProgramFiles%`**（**`%`** 在 bash 中为作业号）。

- **CMD**：`"%ProgramFiles%\Oracle\VirtualBox\VBoxManage.exe" modifyvm default --memory 8192 --cpus 4`
- **PowerShell**：`& "$env:ProgramFiles\Oracle\VirtualBox\VBoxManage.exe" modifyvm default --memory 8192 --cpus 4`
- **Git Bash**：`"/c/Program Files/Oracle/VirtualBox/VBoxManage.exe" modifyvm default --memory 8192 --cpus 4`

**Docker Desktop（WSL2）** 用户在 Desktop **Settings → Resources** 调资源，勿用本节 VirtualBox 步骤。

### 9.2 Codex CLI

装在本机即可；**`curl`/浏览器** 测 API 用 **`docker-machine ip`** 的 **IP + 端口**。

---

## 10. `fixtures/seed.sql`

```bash
docker exec -i dbquery_postgres_1 psql -U postgres -d postgres -v ON_ERROR_STOP=1 < fixtures/seed.sql
```

容器名以 **`docker ps`** 为准。
