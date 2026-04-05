# 快速启动：数据库查询工具

**分支**：`001-db-query-tool` | **日期**：2026-03-29
**运行环境**：Win10 + Docker Toolbox

---

## 前置条件

- Docker Toolbox 已安装并启动（`docker-machine start default`）
- 获取 Docker Toolbox 默认 IP（通常为 `192.168.99.100`）：
  ```bash
  docker-machine ip default
  ```
- 准备好 OpenAI API Key

---

## 目录结构

```
db-query/
├── backend/
│   ├── pyproject.toml
│   ├── Dockerfile
│   ├── .env.example
│   └── app/
├── frontend/
│   ├── package.json
│   ├── Dockerfile
│   └── src/
└── docker-compose.yml
```

---

## 启动步骤

### 1. 配置环境变量

```bash
# 复制后端环境变量模板
cp backend/.env.example backend/.env

# 编辑 backend/.env，填写以下内容：
# OPENAI_API_KEY=sk-xxxxxx
# DB_QUERY_PATH=/root/.db_query
```

### 2. 配置前端 API 地址

```bash
# 编辑 frontend/.env（首次需创建）：
# VITE_API_BASE_URL=http://192.168.99.100:8000
```

### 3. 启动所有服务

```bash
# 在项目根目录执行
docker-compose up --build
```

启动完成后：
- 后端 API：`http://192.168.99.100:8000`
- 前端界面：`http://192.168.99.100:3000`
- API 文档（Swagger）：`http://192.168.99.100:8000/docs`

---

## 验证启动成功

```bash
# 检查后端健康状态
curl http://192.168.99.100:8000/api/v1/dbs
# 预期返回：[]

# 检查前端
# 浏览器打开 http://192.168.99.100:3000，应显示数据库连接列表页
```

---

## 基本使用流程

### Step 1：添加数据库连接

```bash
curl -X PUT http://192.168.99.100:8000/api/v1/dbs/my-db \
  -H "Content-Type: application/json" \
  -d '{"url": "postgres://postgres:postgres@192.168.99.1:5432/mydb"}'
```

> **注意**：在 Docker Toolbox 中，宿主机 IP 通常为 `192.168.99.1`，
> 而非 `localhost`。

### Step 2：加载元数据

```bash
curl http://192.168.99.100:8000/api/v1/dbs/my-db
```

首次调用会连接 PostgreSQL 并缓存元数据，之后调用直接返回缓存。

### Step 3：执行 SQL 查询

```bash
curl -X POST http://192.168.99.100:8000/api/v1/dbs/my-db/query \
  -H "Content-Type: application/json" \
  -d '{"sql": "SELECT * FROM users"}'
```

### Step 4：自然语言生成 SQL

```bash
curl -X POST http://192.168.99.100:8000/api/v1/dbs/my-db/query/natural \
  -H "Content-Type: application/json" \
  -d '{"prompt": "查询用户表中所有邮箱包含 example.com 的用户"}'
```

---

## 常见问题

| 问题 | 原因 | 解决方法 |
|------|------|---------|
| 前端无法连接后端 | `VITE_API_BASE_URL` 配置错误 | 确认 Docker Toolbox IP 并重新 build |
| 数据库连接失败 | 目标 PostgreSQL 不可从 Docker 内部访问 | 使用宿主机 IP `192.168.99.1` 而非 `localhost` |
| LLM 生成失败 | `OPENAI_API_KEY` 未配置或无效 | 检查 `backend/.env` 并重启容器 |
| 元数据加载超时 | PostgreSQL 表数量过多 | 增加后端超时配置；元数据缓存后不再超时 |

---

## docker-compose.yml 参考

```yaml
version: "3.8"

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    env_file:
      - ./backend/.env
    volumes:
      - db_query_data:/root/.db_query

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    env_file:
      - ./frontend/.env
    depends_on:
      - backend

volumes:
  db_query_data:
```
