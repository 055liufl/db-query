# API 接口契约：数据库查询工具

**分支**：`001-db-query-tool` | **日期**：2026-03-29
**基础 URL**：`http://<host>:8000/api/v1`
**协议**：HTTP/1.1，JSON 请求体/响应体
**CORS**：允许所有 Origin（`Access-Control-Allow-Origin: *`）
**认证**：无

---

## 通用约定

- 所有响应 JSON 字段使用 **camelCase**
- 时间格式：UTC ISO 8601（`2026-03-29T00:00:00Z`）
- 错误响应统一格式：

```json
{
  "error": "错误类型标识",
  "message": "用户可读的中文错误描述",
  "detail": "可选的技术细节"
}
```

| HTTP 状态码 | 含义 |
|------------|------|
| 200 | 成功 |
| 201 | 创建成功 |
| 400 | 请求参数错误（如 SQL 非法、URL 格式错误） |
| 404 | 资源不存在（如连接名不存在） |
| 422 | 请求体校验失败（Pydantic 校验错误） |
| 500 | 服务器内部错误（如数据库连接失败） |

---

## 端点定义

### 1. 获取所有数据库连接

```
GET /api/v1/dbs
```

**描述**：返回所有已保存的数据库连接列表。

**请求参数**：无

**响应 200**：
```json
[
  {
    "name": "my-postgres",
    "url": "postgres://user:pass@localhost:5432/mydb",
    "createdAt": "2026-03-29T00:00:00Z",
    "updatedAt": "2026-03-29T00:00:00Z"
  }
]
```

**响应（空列表）**：
```json
[]
```

---

### 2. 添加或更新数据库连接

```
PUT /api/v1/dbs/{name}
```

**描述**：添加新的数据库连接，或更新已有连接的 URL。`name` 作为唯一标识。

**路径参数**：
| 参数 | 类型 | 说明 |
|------|------|------|
| `name` | `string` | 连接名称，仅允许字母/数字/连字符/下划线，1~64 字符 |

**请求体**：
```json
{
  "url": "postgres://postgres:postgres@localhost:5432/postgres"
}
```

**响应 201**（新建）或 **200**（更新）：
```json
{
  "name": "my-postgres",
  "url": "postgres://postgres:postgres@localhost:5432/postgres",
  "createdAt": "2026-03-29T00:00:00Z",
  "updatedAt": "2026-03-29T00:00:00Z"
}
```

**错误 400**（URL 格式不合法）：
```json
{
  "error": "invalid_url",
  "message": "连接 URL 格式不正确，必须以 postgres:// 或 postgresql:// 开头"
}
```

---

### 3. 获取数据库元数据

```
GET /api/v1/dbs/{name}
```

**描述**：返回指定数据库的表和视图结构元数据。若缓存存在则直接返回，
否则实时连接数据库抓取并缓存。

**路径参数**：
| 参数 | 类型 | 说明 |
|------|------|------|
| `name` | `string` | 连接名称 |

**查询参数**：
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `refresh` | `boolean` | `false` | 强制刷新元数据缓存 |

**响应 200**：
```json
{
  "connectionName": "my-postgres",
  "tables": [
    {
      "schemaName": "public",
      "tableName": "users",
      "tableType": "BASE TABLE",
      "columns": [
        {
          "name": "id",
          "dataType": "integer",
          "isNullable": false,
          "columnDefault": "nextval('users_id_seq'::regclass)"
        },
        {
          "name": "email",
          "dataType": "character varying",
          "isNullable": false,
          "columnDefault": null
        }
      ]
    },
    {
      "schemaName": "public",
      "tableName": "active_users",
      "tableType": "VIEW",
      "columns": [
        {"name": "id", "dataType": "integer", "isNullable": true, "columnDefault": null},
        {"name": "email", "dataType": "character varying", "isNullable": true, "columnDefault": null}
      ]
    }
  ],
  "cachedAt": "2026-03-29T00:00:00Z"
}
```

**错误 404**（连接不存在）：
```json
{
  "error": "connection_not_found",
  "message": "未找到名为 'my-postgres' 的数据库连接"
}
```

**错误 500**（数据库连接失败）：
```json
{
  "error": "connection_failed",
  "message": "无法连接到数据库，请检查连接 URL 是否正确",
  "detail": "could not connect to server: Connection refused"
}
```

---

### 4. 执行 SQL 查询

```
POST /api/v1/dbs/{name}/query
```

**描述**：对指定数据库执行 SQL 查询。仅允许 SELECT 语句；若无 LIMIT 子句，
自动追加 `LIMIT 1000`。

**路径参数**：
| 参数 | 类型 | 说明 |
|------|------|------|
| `name` | `string` | 连接名称 |

**请求体**：
```json
{
  "sql": "SELECT * FROM users WHERE email LIKE '%@example.com'"
}
```

**响应 200**：
```json
{
  "sql": "SELECT * FROM users WHERE email LIKE '%@example.com' LIMIT 1000",
  "columns": [
    {"name": "id", "dataType": "integer"},
    {"name": "email", "dataType": "character varying"}
  ],
  "rows": [
    {"id": 1, "email": "alice@example.com"},
    {"id": 2, "email": "bob@example.com"}
  ],
  "rowCount": 2,
  "truncated": false,
  "elapsedMs": 38
}
```

**错误 400**（非 SELECT 语句）：
```json
{
  "error": "forbidden_statement",
  "message": "仅允许执行 SELECT 查询，检测到 DROP 语句"
}
```

**错误 400**（SQL 语法错误）：
```json
{
  "error": "syntax_error",
  "message": "SQL 语法错误：第 1 行第 8 列附近存在语法问题",
  "detail": "Expected table name after FROM"
}
```

**错误 400**（多条语句）：
```json
{
  "error": "multiple_statements",
  "message": "每次仅允许提交一条 SQL 语句"
}
```

---

### 5. 自然语言生成 SQL

```
POST /api/v1/dbs/{name}/query/natural
```

**描述**：将自然语言描述发送给 LLM，结合数据库元数据生成 SQL 查询语句。
返回生成的 SQL，不自动执行。

**路径参数**：
| 参数 | 类型 | 说明 |
|------|------|------|
| `name` | `string` | 连接名称 |

**请求体**：
```json
{
  "prompt": "查询最近注册的 10 名用户的邮箱"
}
```

**响应 200**：
```json
{
  "generatedSql": "SELECT email FROM users ORDER BY created_at DESC LIMIT 10"
}
```

**错误 404**（连接或元数据不存在）：
```json
{
  "error": "metadata_not_found",
  "message": "尚未加载该数据库的元数据，请先访问 GET /api/v1/dbs/{name} 获取元数据"
}
```

**错误 500**（LLM 服务不可用）：
```json
{
  "error": "llm_unavailable",
  "message": "AI 服务暂时不可用，请稍后重试或手动编写 SQL"
}
```

---

## 接口摘要表

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/v1/dbs` | 获取所有数据库连接列表 |
| PUT | `/api/v1/dbs/{name}` | 添加或更新数据库连接 |
| GET | `/api/v1/dbs/{name}` | 获取数据库元数据（含缓存） |
| POST | `/api/v1/dbs/{name}/query` | 执行 SQL 查询 |
| POST | `/api/v1/dbs/{name}/query/natural` | 自然语言生成 SQL |
