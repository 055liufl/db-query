# Codex CLI 与 Docker Toolbox

本文说明如何在 **Docker Toolbox** 运行本仓库（db-query）时配合使用 **OpenAI Codex CLI**（终端侧工具）。

> Docker 启动、环境变量、网络排障等详见 **[`docker-troubleshooting.md`](./docker-troubleshooting.md)**（单一事实来源）。

## 1. Codex CLI 跑在宿主机，不是容器内

- **Codex CLI**（如 `@openai/codex`）安装在 **Windows 本机**（PowerShell / CMD / Git Bash）。
- 它在 **本机磁盘上的仓库** 里读代码、改文件、执行命令（例如 `docker-compose up`）。
- **一般不需要** 把 Codex 装进 `backend` 镜像。

## 2. 与应用内 `OPENAI_API_KEY` 的区别

| 用途 | 说明 |
|------|------|
| **Codex CLI** | 本机 ChatGPT / Codex 登录，用于终端里写代码、跑命令。 |
| **应用内「自然语言生成 SQL」** | 后端通过 **`OPENAI_API_KEY`** 调 OpenAI API（与 Codex 是否安装无关）。 |

两者独立。`OPENAI_API_KEY` 的配置方式见 **[`docker-troubleshooting.md` §5](./docker-troubleshooting.md#5-环境变量backendenv)**。

## 3. 不推荐

在镜像内再安装 Codex CLI：镜像变大，Toolbox 上还可能遇到权限/网络问题，一般无必要。
