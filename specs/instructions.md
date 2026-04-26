# Instructions

## constitution

- 后端使用 Ergonomic Python 风格来编写代码, 前端使用 typescript
- 前端和后端要有严格的类型标注
- 使用 pydantic 来定义数据模型
- 所有后端生成的 JSON 数据, 使用 camelCase 格式
- 不需要使用 authentication, 任何用户都可以使用


## 基本思路

这是一个数据库查询工具, 用户可以添加一个 db url, 系统会连接到数据库, 获取数据库的 metadata, 然后将数据库中的 table 和 view 的信息展示出来, 然后用户可以自己输入 sql 查询, 也可以通过自然语言来生成 sql 查询


基本想法:
- 数据库连接字符串和数据库的 metadata 都会存储到 sqlite 数据库中. 我们可以根据 postgres 的功能来查询 系统中的表和视图的信息, 然后用 LLM 来将这些信息转换成 json 格式, 然后保存到 sqlite 数据库中. 这个信息 以后可以复用
- 当用户使用 LLM 来生成 sql 查询时, 我们可以将系统中的表和视图的信息作为 context 传递给 LLM, 然后 LLM 会根据这些信息来生成 sql 查询
- 任何输入的 sql 语句, 都需要经过 sqlparser 解析, 确保语法正确, 并且仅包含 select 语句. 如果语法不正确, 需要给出错误信息
- 如果查询不包含 limit 子句, 则默认添加 limit 1000 子句
- 输出格式是 json, 前端将其组织成表格, 并显示出来


## 计划

技术栈与 API 契约详见 [`plan.md`](./001-db-query-tool/plan.md) 和 [`contracts/api.md`](./001-db-query-tool/contracts/api.md)。

运行环境为 Ubuntu 20.04 + Docker（亦兼容 Win10 + Docker Toolbox）。


## 测试
运行后端和前端, 根据 @test.rest 用 curl 测试后端已实现的路由; 然后用 playwright 打开前端进行测试, 任何测试问题, think ultra hard and fix



## 前端风格

使用 @.cursor/rulesstyle.md 中的风格, 学习 ./site 中 token 的定义, 优化整体的 UI 和 UX



## 主页

主页可以添加,删除,编辑,显示所有的数据库连接信息, 并且可以点击数据库连接, 进入到查询界面.



## 侧边栏

侧边栏可以放所有的数据库, 并且把添加数据库,删除已有数据库的功能放在侧边栏.
侧边栏也要使用新的 token 风格. 然后主页直接显示第一个数据库的 metadata 信息和查询界面, 这样用户可以减少一次点击进入到 database display 页面.一个页面囊括所有功能.
