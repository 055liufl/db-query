# 数据模型：数据库查询工具

**分支**：`001-db-query-tool` | **日期**：2026-03-29

## 实体关系概览

```
DbConnection  1 ──── 0..1  DbMetadata
DbConnection  1 ──── *     QueryExecution
```

---

## 实体定义

### 1. DbConnection（数据库连接）

存储用户添加的数据库连接信息，持久化到 SQLite。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `name` | `str` | PRIMARY KEY，唯一，非空 | 用户自定义连接名称（URL slug 友好） |
| `url` | `str` | 非空 | 数据库连接 URL，如 `postgres://user:pass@host:5432/db` 或 `mysql://user:pass@host:3306/db` |
| `created_at` | `datetime` | 非空，自动填充 | 创建时间（UTC ISO 8601） |
| `updated_at` | `datetime` | 非空，自动更新 | 最后更新时间（UTC ISO 8601） |

**校验规则**：
- `name`：仅允许字母、数字、连字符、下划线；长度 1~64 字符
- `url`：必须以 `postgres://`、`postgresql://` 或 `mysql://` 开头

**Pydantic 模型**：
```python
class DbConnection(AppBaseModel):
    name: str
    url: str
    created_at: datetime
    updated_at: datetime
```

**SQLite 表**：
```sql
CREATE TABLE IF NOT EXISTS db_connections (
    name        TEXT PRIMARY KEY,
    url         TEXT NOT NULL,
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);
```

---

### 2. DbMetadata（数据库元数据缓存）

缓存从 PostgreSQL 或 MySQL 抓取的表/视图结构信息，与连接一对一关联。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `connection_name` | `str` | PRIMARY KEY，外键 → `db_connections.name` | 所属连接名 |
| `metadata_json` | `str` | 非空 | 序列化的元数据 JSON 字符串 |
| `cached_at` | `datetime` | 非空 | 缓存写入时间（UTC ISO 8601） |

**元数据 JSON Schema**（`metadata_json` 反序列化后的结构）：
```python
class ColumnInfo(AppBaseModel):
    name: str
    data_type: str
    is_nullable: bool
    column_default: str | None = None

class TableInfo(AppBaseModel):
    schema_name: str     # camelCase: schemaName
    table_name: str      # camelCase: tableName
    table_type: str      # 'BASE TABLE' | 'VIEW'
    columns: list[ColumnInfo]

class DbMetadata(AppBaseModel):
    connection_name: str  # camelCase: connectionName
    tables: list[TableInfo]
    cached_at: datetime   # camelCase: cachedAt
```

**SQLite 表**：
```sql
CREATE TABLE IF NOT EXISTS db_metadata (
    connection_name  TEXT PRIMARY KEY
        REFERENCES db_connections(name) ON DELETE CASCADE,
    metadata_json    TEXT NOT NULL,
    cached_at        TEXT NOT NULL
);
```

---

### 3. QueryExecution（查询执行，仅内存/响应，不持久化）

查询请求和响应的临时数据模型，不写入 SQLite。

**请求模型**：
```python
class QueryRequest(AppBaseModel):
    sql: str              # 用户输入的原始 SQL

class NaturalQueryRequest(AppBaseModel):
    prompt: str           # 自然语言描述
```

**响应模型**：
```python
class QueryColumn(AppBaseModel):
    name: str
    data_type: str        # camelCase: dataType

class QueryResult(AppBaseModel):
    sql: str              # 实际执行的 SQL（含自动追加的 LIMIT）
    columns: list[QueryColumn]
    rows: list[dict]      # 每行数据，key 为字段名
    row_count: int        # camelCase: rowCount
    truncated: bool       # 是否因 LIMIT 被截断
    elapsed_ms: int       # camelCase: elapsedMs，查询耗时（毫秒）

class NaturalQueryResult(AppBaseModel):
    generated_sql: str    # camelCase: generatedSql，LLM 生成的 SQL
```

**错误响应模型**：
```python
class ErrorResponse(AppBaseModel):
    error: str            # 错误类型
    message: str          # 用户可读的错误描述
    detail: str | None = None  # 技术细节（可选）
```

---

## 状态流转

### 数据库连接状态

```
[未连接] ──add URL──→ [已保存] ──metadata fetch──→ [就绪]
                                    ↓ 失败
                               [连接失败]（错误提示，连接记录保留）
```

### 元数据缓存状态

```
[无缓存] ──首次连接──→ [缓存中] ──成功──→ [已缓存]
[已缓存] ──用户刷新──→ [缓存中] ──成功──→ [已缓存]
```

---

## API 响应示例（camelCase）

### GET /api/v1/dbs 响应
```json
[
  {
    "name": "my-db",
    "url": "postgres://user:pass@localhost:5432/mydb",
    "createdAt": "2026-03-29T00:00:00Z",
    "updatedAt": "2026-03-29T00:00:00Z"
  },
  {
    "name": "my-mysql",
    "url": "mysql://root@localhost:3306/todo_db",
    "createdAt": "2026-04-15T00:00:00Z",
    "updatedAt": "2026-04-15T00:00:00Z"
  }
]
```

### GET /api/v1/dbs/{name} 响应
```json
{
  "connectionName": "my-db",
  "tables": [
    {
      "schemaName": "public",
      "tableName": "users",
      "tableType": "BASE TABLE",
      "columns": [
        {"name": "id", "dataType": "integer", "isNullable": false},
        {"name": "email", "dataType": "character varying", "isNullable": false}
      ]
    }
  ],
  "cachedAt": "2026-03-29T00:00:00Z"
}
```

### POST /api/v1/dbs/{name}/query 响应
```json
{
  "sql": "SELECT * FROM users LIMIT 1000",
  "columns": [
    {"name": "id", "dataType": "integer"},
    {"name": "email", "dataType": "character varying"}
  ],
  "rows": [
    {"id": 1, "email": "alice@example.com"}
  ],
  "rowCount": 1,
  "truncated": false,
  "elapsedMs": 42
}
```
