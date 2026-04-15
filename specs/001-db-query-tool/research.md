# 研究报告：数据库查询工具

**分支**：`001-db-query-tool` | **日期**：2026-03-29

## 1. FastAPI + asyncpg 异步连接 PostgreSQL

**决策**：使用 `asyncpg` 直接异步连接 PostgreSQL，而非 SQLAlchemy ORM。

**理由**：
- 本工具只做只读查询，不需要 ORM 的对象映射功能
- `asyncpg` 是 Python 最快的 PostgreSQL 驱动，原生异步
- 查询结果直接返回为字典列表，便于序列化为 JSON

**替代方案评估**：
- SQLAlchemy async：功能过重，引入不必要的 ORM 层
- psycopg3 async：性能相近，但 asyncpg 生态更成熟
- databases 库：底层仍是 asyncpg，增加无必要的抽象层

**实现要点**：
```python
import asyncpg

async def execute_query(url: str, sql: str) -> list[dict]:
    conn = await asyncpg.connect(url)
    try:
        rows = await conn.fetch(sql)
        return [dict(row) for row in rows]
    finally:
        await conn.close()
```

---

## 1b. aiomysql 异步连接 MySQL

**决策**：使用 `aiomysql` 异步连接 MySQL，与 asyncpg 并列作为第二数据库驱动。
系统根据连接 URL scheme（`postgres://` vs `mysql://`）自动选择驱动。

**理由**：
- `aiomysql` 基于 PyMySQL，纯 Python 实现，无需编译 C 扩展，Docker 镜像无额外系统依赖
- 原生 asyncio 支持，与 FastAPI 异步架构一致
- DictCursor 可直接返回字典列表，便于序列化为 JSON
- MySQL URL 通过 `urllib.parse.urlparse` 解析为 host/port/user/password/db 参数

**替代方案评估**：
- asyncmy：性能更高（Cython），但需要编译环境，Docker slim 镜像不友好
- SQLAlchemy async + aiomysql：引入不必要的 ORM 抽象
- mysql-connector-python：官方驱动但无原生 asyncio 支持

**实现要点**：
```python
import aiomysql

async def execute_query(url: str, sql: str) -> list[dict]:
    params = _parse_mysql_url(url)  # urlparse -> host/port/user/password/db
    conn = await aiomysql.connect(**params)
    try:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(sql)
            return await cur.fetchall()
    finally:
        conn.close()
```

---

## 2. sqlglot SQL 解析与安全校验

**决策**：使用 `sqlglot` 解析 SQL，验证仅包含 SELECT 语句，并自动注入 LIMIT。
解析和生成时根据连接的数据库类型选择对应方言（`dialect="postgres"` 或 `dialect="mysql"`）。

**理由**：
- sqlglot 支持多种数据库方言（默认 ANSI，可指定 `dialect="postgres"` 或 `dialect="mysql"`）
- 提供完整的 AST 解析，可精准检测语句类型
- 纯 Python 实现，无系统级依赖
- MySQL 方言正确处理反引号（`` ` ``）标识符

**实现要点**：
```python
import sqlglot
from sqlglot import exp

def validate_and_limit(sql: str, dialect: str = "postgres") -> str:
    statements = sqlglot.parse(sql, dialect=dialect)
    if len(statements) != 1:
        raise ValueError("仅允许提交单条 SQL 语句")
    stmt = statements[0]
    if not isinstance(stmt, exp.Select):
        raise ValueError("仅允许执行 SELECT 查询")
    if stmt.args.get("limit") is None:
        stmt = stmt.limit(1000)
    return stmt.sql(dialect=dialect)
```

**替代方案评估**：
- 正则表达式匹配：无法处理嵌套、注释、子查询等复杂情况，不可靠
- pglast：仅支持 PostgreSQL，且需要 C 扩展
- antlr4 SQL 语法：实现成本过高

---

## 3. 数据库元数据查询方案

**决策**：通过 `information_schema`（SQL 标准）查询表和视图结构，结果以 JSON
缓存到 SQLite。PostgreSQL 过滤 `pg_catalog` 和 `information_schema` 系统 schema；
MySQL 过滤 `information_schema`、`mysql`、`performance_schema`、`sys` 系统 schema。

**核心查询**：
```sql
-- 获取所有表和视图
SELECT
    table_schema,
    table_name,
    table_type
FROM information_schema.tables
WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
ORDER BY table_schema, table_name;

-- 获取字段信息
SELECT
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_schema = $1 AND table_name = $2
ORDER BY ordinal_position;
```

**理由**：`information_schema` 是 SQL 标准，PostgreSQL 和 MySQL 均支持，跨版本
兼容性好。PostgreSQL 不依赖 pg_catalog 私有表，升级安全；MySQL 的 `information_schema`
同样提供完整的表和列元数据。

**元数据 JSON 结构**（缓存到 SQLite）：
```json
{
  "tables": [
    {
      "schema": "public",
      "name": "users",
      "type": "BASE TABLE",
      "columns": [
        {"name": "id", "type": "integer", "nullable": false},
        {"name": "email", "type": "character varying", "nullable": false}
      ]
    }
  ]
}
```

---

## 4. SQLite 存储方案（aiosqlite）

**决策**：使用 `aiosqlite` 作为 SQLite 的异步驱动，存储路径 `~/.db_query/db_query.db`。

**理由**：
- FastAPI 全异步架构，需要异步 SQLite 驱动
- aiosqlite 是 asyncio 友好的 SQLite 封装，API 简洁
- 无需 SQLAlchemy，直接执行 DDL/DML

**表结构**：
```sql
CREATE TABLE IF NOT EXISTS db_connections (
    name        TEXT PRIMARY KEY,
    url         TEXT NOT NULL,
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS db_metadata (
    connection_name  TEXT PRIMARY KEY REFERENCES db_connections(name),
    metadata_json    TEXT NOT NULL,
    cached_at        TEXT NOT NULL
);
```

---

## 5. OpenAI SDK 自然语言生成 SQL

**决策**：使用 `openai` Python SDK（v1.x），调用 `gpt-4o-mini`（可配置），
将数据库元数据作为系统 prompt 上下文，用户自然语言作为用户消息。

**Prompt 设计策略**（根据数据库类型动态切换）：
```
System:
你是 {PostgreSQL|MySQL} SQL 专家。以下是数据库的表结构信息：
{metadata_json}

规则：
1. 只生成 SELECT 查询
2. 不要添加解释文字，只输出 SQL
3. 使用标准 {PostgreSQL|MySQL} 语法

User:
{用户自然语言描述}
```

**理由**：
- 将元数据放在系统 prompt 中，每次对话均可复用上下文
- 要求 LLM 只输出 SQL，便于直接填入编辑器
- gpt-4o-mini 成本低，对结构化 SQL 生成质量足够

**错误处理**：
- API 超时（30s）→ 返回错误提示，不阻塞用户
- 生成内容非 SQL → 前端展示原始响应，由用户决定是否使用
- LLM 不可用时 → 用户仍可手动编写 SQL

---

## 6. Docker Toolbox 部署方案

**决策**：使用 `docker-compose` 编排前后端，后端暴露 `8000` 端口，
前端开发服务器暴露 `3000` 端口，通过 Docker Toolbox 默认 IP `192.168.99.100` 访问。

**关键配置**：
- 后端环境变量：`OPENAI_API_KEY`、`DB_QUERY_PATH`（SQLite 路径，默认 `~/.db_query`）
- 前端环境变量：`VITE_API_BASE_URL=http://192.168.99.100:8000`
- SQLite 文件通过 Docker volume 挂载到宿主机，保证数据持久化

**CORS 配置**：
```python
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**替代方案评估**：
- 直接宿主机运行：Windows 环境 Python 版本管理复杂，Docker 更可控
- Docker Desktop：用户明确要求 Docker Toolbox，不替换

---

## 7. Pydantic v2 camelCase 配置

**决策**：所有 Pydantic 模型使用全局 `alias_generator` 自动生成 camelCase 别名。

**实现**：
```python
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

class AppBaseModel(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=to_camel,
    )

# FastAPI 路由使用 response_model 时自动序列化为 camelCase
```

**理由**：定义一个公共基类 `AppBaseModel`，所有业务模型继承它，
避免在每个模型重复配置，符合 DRY 原则。
