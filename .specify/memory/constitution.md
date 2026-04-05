<!--
同步影响报告
=============
版本变更：（无）→ 1.0.0
新增原则：
  - 原则一：后端 Ergonomic Python 风格 / 前端 TypeScript
  - 原则二：严格类型标注
  - 原则三：Pydantic 数据模型
  - 原则四：后端 JSON 使用 camelCase 格式
  - 原则五：无需认证，开放访问
新增章节：技术栈约束、开发工作流、治理规范
删除章节：无
模板更新状态：
  - .specify/templates/plan-template.md   ✅ 无需更新（通用模板）
  - .specify/templates/spec-template.md   ✅ 无需更新（通用模板）
  - .specify/templates/tasks-template.md  ✅ 无需更新（通用模板）
延迟待办事项：
  - TODO(RATIFICATION_DATE)：项目正式立项日期未知，暂以首次提交日期 2026-03-29 代替
-->

# DB-Query 数据库查询工具 项目宪法

## 核心原则

### 一、后端 Ergonomic Python 风格 / 前端 TypeScript

后端代码 MUST 遵循 Ergonomic Python 风格，即：代码可读性优先，善用 Python
惯用法（列表推导、上下文管理器、数据类等），避免过度工程化；前端代码 MUST 使用
TypeScript，不得使用纯 JavaScript 文件（`.js`）。

**理由**：统一语言风格可降低认知负担，提升团队协作效率，并充分利用各自生态的
类型安全优势。

### 二、严格类型标注

前端和后端的所有公开接口、函数签名、模型字段 MUST 携带完整的类型标注。后端
MUST 使用 Python 类型提示（`typing` / PEP 604），前端 MUST 使用 TypeScript
显式类型（禁止使用 `any`，除非有充分的注释说明）。

**理由**：严格类型标注在编译/静态分析阶段即可捕获大量错误，显著减少运行时
问题，并为 IDE 自动补全提供基础。

### 三、Pydantic 数据模型

所有后端数据模型（请求体、响应体、数据库实体映射）MUST 使用 Pydantic（v2+）
进行定义与校验。禁止使用裸字典或未经校验的数据结构作为业务对象。

**理由**：Pydantic 提供运行时数据校验、序列化和文档自动生成，与 FastAPI
深度集成，是保证数据一致性的最简方案。

### 四、后端 JSON 使用 camelCase 格式

所有后端 API 返回的 JSON 字段名 MUST 使用 camelCase 格式（如 `tableList`、
`connectionUrl`），不得使用 snake_case 或其他格式。Pydantic 模型 MUST 配置
`model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)`
或等效方案以自动完成转换。

**理由**：前端 JavaScript/TypeScript 社区普遍采用 camelCase，统一格式可避免
前后端手动转换字段名的繁琐工作。

### 五、无需认证，开放访问

本系统不实现任何身份认证或授权机制。所有 API 端点对任意来源的请求均开放。
MUST NOT 引入 JWT、Session、OAuth 等认证中间件。

**理由**：本工具定位为内部开发/分析工具，简化访问控制可降低复杂度，加快
迭代速度。若未来需要多租户或生产环境部署，可在此原则基础上进行修订。

## 技术栈约束

本节列出项目强制使用的技术依赖，所有实现 MUST 在此范围内选型，不得随意
引入同类替代库（如需替换，须修订本宪法）。

**后端**：
- 运行时：Python（通过 `uv` 管理依赖）
- Web 框架：FastAPI
- SQL 解析：sqlglot（用于语法校验，确保仅含 SELECT 语句）
- LLM 集成：openai SDK
- 本地存储：SQLite（存储数据库连接信息与 metadata 缓存）

**前端**：
- 框架：React + Refine 5
- 样式：Tailwind CSS + Ant Design
- SQL 编辑器：Monaco Editor

**运行环境**：Win10 + Docker Toolbox

**SQL 安全约束**：所有用户输入的 SQL MUST 经过 sqlglot 解析校验，仅允许
SELECT 语句通过；若查询缺少 `LIMIT` 子句，MUST 自动追加 `LIMIT 1000`。

**输出格式**：所有查询结果 MUST 以 JSON 格式返回，前端将其渲染为表格展示。

## 开发工作流

- 后端新增接口时，MUST 同步更新 Pydantic 响应模型，确保 camelCase 别名
  配置正确。
- 前端调用 API 时，MUST 为响应数据定义对应的 TypeScript 接口/类型，禁止
  使用 `any` 接收 API 数据。
- LLM 生成 SQL 的流程：将目标数据库的表/视图 metadata 作为 context 传入
  LLM，LLM 返回 SQL 后 MUST 经过 sqlglot 二次校验方可执行。
- metadata 缓存策略：首次连接数据库时，通过查询系统表获取 metadata，经 LLM
  转换为 JSON 后持久化到 SQLite，后续复用缓存以减少重复查询。

## 治理规范

- 本宪法是项目所有技术决策的最高准则，其效力高于任何单次 PR 描述或口头约定。
- 修订流程：任何原则的变更 MUST 更新本文件并记录版本号、修订日期及修订原因。
- 版本策略：遵循语义化版本——MAJOR（原则删除或不兼容重定义）、MINOR（新增
  原则或章节）、PATCH（措辞优化、错别字修正）。
- 合规审查：每个 Feature 的 `plan.md` 中 MUST 包含 "Constitution Check" 章节，
  逐条核对相关原则的遵守情况。
- 复杂度违规须在对应 `plan.md` 的 "Complexity Tracking" 表格中记录违规项、
  必要性说明及已排除的更简方案。

**版本**：1.0.0 | **批准日期**：2026-03-29 | **最后修订**：2026-03-29
