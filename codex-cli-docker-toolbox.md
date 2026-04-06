# Codex CLI 与 Docker Toolbox

本文说明如何在 **Docker Toolbox** 运行本仓库（db-query）时配合使用 **OpenAI Codex CLI**（终端侧工具）。

## 1. Codex CLI 跑在宿主机，不是容器内

- **Codex CLI**（如 `@openai/codex`）安装在 **Windows 本机**（PowerShell / CMD / Git Bash）。
- 它在 **本机磁盘上的仓库** 里读代码、改文件、执行命令（例如 `docker-compose up`）。
- **一般不需要** 把 Codex 装进 `backend` 镜像。

## 2. 推荐用法

1. 在本机安装 Codex CLI（按官方文档，例如 `npm i -g @openai/codex` 等）。
2. 终端 `cd` 到本仓库根目录（含 `docker-compose.yml`）。
3. 启动服务：`docker-compose up --build`（或按需只起部分服务）。
4. 在 **Windows 浏览器** 访问（Toolbox 下不要误用本机 `localhost` 当作虚拟机地址）：
   - 前端：`http://<docker-machine-ip>:3000`
   - API：`http://<docker-machine-ip>:8000`  
   其中 `<docker-machine-ip>` 使用：`docker-machine ip default`。

**小结**：程序在 Toolbox 的 Docker 里跑；Codex 在本机帮你改代码、下命令；测接口时 `curl` 等也要指向 **上述 IP + 端口**。

## 3. 若希望用 `localhost` 访问

二选一：

- **端口映射到本机**：compose 已映射 `8000`/`3000` 时，在 VirtualBox 的 `default` 虚拟机里配置 **端口转发**（如 8000→8000），Windows 上才可用 `http://127.0.0.1:8000`。
- **不配端口转发**：统一使用 `docker-machine ip` 的结果访问。

更细的排障见仓库根目录 **`docker-troubleshooting.md`**。

## 4. 与 Codex 的区别、以及 `OPENAI_API_KEY` 怎么配

| 用途 | 说明 |
|------|------|
| **Codex CLI** | 本机 ChatGPT / Codex 登录，用于终端里写代码、跑命令。 |
| **应用内「自然语言生成 SQL」** | 后端通过 **`OPENAI_API_KEY`** 调 OpenAI API（与 Codex 是否安装无关）。 |

两者独立。

### 4.1 后端如何读取

- 配置类：`backend/app/core/config.py` 中 `openai_api_key`，环境变量名为 **`OPENAI_API_KEY`**（与 `.env` / 系统环境变量对应）。
- 本地用 **`uv run`** 在 `backend/` 目录启动时：可在同目录放置 **`backend/.env`**，写入一行：  
  `OPENAI_API_KEY=sk-...`  
  （参考 **`backend/.env.example`**，勿把含真密钥的 `.env` 提交到 Git。）

### 4.2 Docker / docker-compose 里怎么配

- 本仓库在 **`docker-compose.yml`** 的 **`backend`** 服务上使用 **`env_file: ./backend/.env`**，把宿主机 **`backend/.env`** 中的变量注入容器环境（与 **`uv run`** 使用同一份文件内容，无需再 bind-mount **`/app/.env`**）。
- 在 **`backend/.env`** 中填写 **`OPENAI_API_KEY`**（及可选 **`OPENAI_BASE_URL`**），保存后 **`docker-compose up -d --force-recreate backend`**。
- 不配或留空：自然语言生成 SQL 不可用，**手动写 SQL 仍可用**。更细的说明见 **`docker-troubleshooting.md`**。

### 4.3 临时一条命令（仅本机 `uv run`，非 Docker）

在 **`backend/`** 目录启动前于 shell 设置（PowerShell 示例）：

```powershell
$env:OPENAI_API_KEY="sk-..."
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## 5. 不推荐

在镜像内再安装 Codex CLI：镜像变大，Toolbox 上还可能遇到权限/网络问题，一般无必要。

---

*由对话整理写入本文件，便于本地留存。*
