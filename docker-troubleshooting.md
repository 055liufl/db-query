# Docker 排障与约定（db-query）

与 **`docker-compose.yml`**、**`backend/Dockerfile`**、**`frontend/src/services/api.ts`** 当前实现一致。中文请用 UTF-8 保存；**`docker-compose.yml` 内勿写中文注释**（旧版 Windows `docker-compose` 用 GBK 读 YAML 会报错）。

---

## 1. 旧版 `docker-compose` 与 YAML

| 问题 | 处理 |
|------|------|
| `UnicodeDecodeError: 'gbk' codec can't decode` | 注释仅用 ASCII；或改用 **Docker Compose V2**（`docker compose`） |
| `${VAR:-}` / invalid interpolation | docker-compose 1.x 不支持；本仓库已去掉；密钥在运行环境中配置 |
| 版本 | 使用 **`version: "3.3"`** 兼容 Toolbox |

---

## 2. 构建 `backend` 镜像（仅 `RUN pip install ...` 阶段）

| 现象 | 处理 |
|------|------|
| `Temporary failure in name resolution` | VM 内修 DNS：`docker-machine ssh default` → `sudo sh -c 'echo nameserver 8.8.8.8 > /etc/resolv.conf'` → 再 **`docker-compose build --no-cache backend`** |
| **`RuntimeError: can't start new thread`（pip/Rich 进度条）** | 已 **`PIP_PROGRESS_BAR=off`**、**`--progress-bar off`**；仍失败则加大 VM 资源或改用本机 **`uv run`**（见表末） |
| `ReadTimeoutError` / `files.pythonhosted.org` | 已去掉 **`pip install -U pip`**；已 **`PIP_DEFAULT_TIMEOUT=300`**、**`--default-timeout 300 --retries 10`** |
| 仍超时/拉不动 | 构建加：`--build-arg PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple --build-arg PIP_TRUSTED_HOST=pypi.tuna.tsinghua.edu.cn` |
| 不想在容器里构建后端 | `cd backend && uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000` |

---

## 3. PostgreSQL 与连接串

**单独起库**：`docker-compose up -d postgres`。**`docker ps`** 须见 **`0.0.0.0:5432->5432/tcp`**；若只有 **`5432/tcp`** 无 **`->`**，宿主机连不上，需在该项目的 compose 里映射 **`ports`**。

| 环境 | 连接串 host 常用 |
|------|------------------|
| Docker Desktop | `127.0.0.1` |
| Docker Toolbox | **`docker-machine ip default`**（如 `192.168.99.100`） |

**`[WinError 1225]`**：对端未监听或 host/port 错。

**Backend 跑在 `docker-compose` 的容器里时**：保存到应用里的 PostgreSQL URL 里 **host 须用服务名 `postgres`**（与 compose 中服务名一致），例如 **`postgresql://postgres:postgres@postgres:5432/postgres`**。若写成 **`127.0.0.1`** 或 **`localhost`**，在容器内指向的是 **backend 自己**，不是数据库容器，执行查询会失败（接口会返回 **`query_failed`**，**`detail`** 里多为连接错误）。

**`curl` 测 `POST /api/v1/dbs/{name}/query` 若 HTTP 500**：看响应 JSON 里的 **`message` / `detail`**；已重建 backend 后仍只有纯文本 **`Internal Server Error`** 时，用 **`docker logs dbquery_backend_1`** 看 Traceback。

---

## 4. 浏览器访问前端与 API 地址

- **用 `http://<虚拟机IP>:3000` 打开页面**时，API 必须在浏览器里可达。若写死 **`http://localhost:8000`**，Toolbox 下常连不到映射在 VM 上的 backend，会出现：
  - 保存连接等：**「请求失败」**；
  - 查询页（如 **`/query/postgres`**）点「执行」：**「执行失败：Failed to fetch」**（浏览器 **`fetch`** 未建立连接，多为 API 基址错或后端未起，一般**不是** SQL 语法问题）。
- **仓库约定**：未设置 **`VITE_API_BASE_URL`** 时，**`api.ts`** 使用 **当前页面的主机名 + `:8000`**（例：`192.168.99.100:3000` → `http://192.168.99.100:8000`）。compose 的 **frontend** 不再默认写 **`localhost:8000`**。
- **仍 Failed to fetch**：确认 **`http://<同主机>:8000/docs`** 能打开，并按 **§5、§6** 查 backend 是否 **Up**。
- **自定义 API 基址**（HTTPS 反代等）：设置 **`VITE_API_BASE_URL`** 并重建前端。

---

## 5. `http://<IP>:8000` 无法打开 / `ERR_CONNECTION_REFUSED`

表示 **8000 上无进程监听**（backend 未起、已退出或未映射端口）。

1. **`docker ps -a`** 看 **`dbquery_backend_1`** 是否为 **Up**，是否有 **`0.0.0.0:8000->8000/tcp`**。  
2. 若 **Exited**：**`docker logs dbquery_backend_1`**。  
3. **端口被其它容器占用**：停冲突服务或改 **`docker-compose.yml`** 的 **`ports`**，并与 **`VITE_API_BASE_URL`**（若使用）一致。

---

## 6. `dbquery_backend_1` 启动失败 / `Exited (3)`

**先查**：**`docker logs dbquery_backend_1`**。

| 原因 | 仓库处理 |
|------|----------|
| **uvloop / httptools** 在弱 VM 上不稳 | **`Dockerfile`** 使用 **`python -m uvicorn ... --loop asyncio --http h11`** |
| **`RuntimeError: can't start new thread`** 在 **`aiosqlite.connect` / `init_db`**（运行时，非 pip） | **`aiosqlite`** 会建后台线程；极紧的 VM 可能失败。已改为标准库 **`sqlite3`**（**`app/storage/sqlite.py`**），**`pyproject.toml`** 已移除 **`aiosqlite`** |

重建：**`docker-compose build --no-cache backend && docker-compose up -d backend`**。

---

## 7. `fixtures/seed.sql`

```bash
docker exec -i dbquery_postgres_1 psql -U postgres -d postgres -v ON_ERROR_STOP=1 < fixtures/seed.sql
```

容器名以 **`docker ps`** 为准；用于配合 **`fixtures/test.rest`** 等示例。
