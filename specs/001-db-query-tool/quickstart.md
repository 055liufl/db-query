# 快速启动：数据库查询工具

**日期**：2026-03-29
**运行环境**：Ubuntu 20.04 + Docker（亦兼容 Win10 + Docker Toolbox）

> 完整的启动步骤、环境变量配置、排障指南见仓库根目录 **[`README.md`](../../README.md)** 和 **[`docker-troubleshooting.md`](../../docker-troubleshooting.md)**。

---

## 三步启动

```bash
# 1. 准备环境变量
cp backend/.env.example backend/.env
# 编辑 backend/.env，填写 OPENAI_API_KEY（可选，仅自然语言 SQL 需要）

# 2. 启动所有服务（postgres + mysql + backend + frontend）
docker-compose up --build

# 3. 访问
# 前端：http://<主机IP>:3000
# API / Swagger：http://<主机IP>:8000/docs
```

---

## 基本使用流程

### Step 1：添加数据库连接

在前端左侧点击「添加连接」，填写：

| 数据库 | 连接 URL（Docker Compose 内部） |
|--------|-------------------------------|
| PostgreSQL | `postgres://postgres:postgres@postgres:5432/postgres` |
| MySQL (interview_db) | `mysql://root:root@mysql:3306/interview_db` |

### Step 2：浏览元数据

点击已添加的连接，左侧面板自动加载表/视图/列信息。

### Step 3：执行查询

在 SQL 编辑器中编写 `SELECT` 语句，点击「Execute Query」。也可在「自然语言」栏输入描述，点击「生成 SQL」自动填入编辑器。

---

## 相关文档

| 文档 | 说明 |
|------|------|
| [`README.md`](../../README.md) | 项目概览、技术栈、测试、API 摘要 |
| [`docker-troubleshooting.md`](../../docker-troubleshooting.md) | Docker 启动、环境变量、网络、LLM、MySQL 排障 |
| [`contracts/api.md`](./contracts/api.md) | 完整 API 契约（请求/响应示例、错误码） |
| [`fixtures/test.rest`](../../fixtures/test.rest) | REST Client 测试用例（PostgreSQL + MySQL） |
