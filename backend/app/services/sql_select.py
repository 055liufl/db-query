from __future__ import annotations

import sqlglot
from sqlglot import exp
from sqlglot.errors import ParseError


def parse_single_select_statement(sql: str, *, dialect: str = "postgres") -> exp.Expression:
    """Parse exactly one SELECT (or WITH wrapping SELECT). Raises ValueError with API-facing messages."""
    try:
        statements = sqlglot.parse(sql, dialect=dialect)
    except ParseError as e:
        msg = f"SQL 语法错误：{e}"
        raise ValueError(msg) from e
    if len(statements) != 1:
        msg = "每次仅允许提交一条 SQL 语句"
        raise ValueError(msg)
    stmt = statements[0]
    if isinstance(stmt, exp.Union):
        msg = "暂不支持 UNION 查询"
        raise ValueError(msg)
    if not isinstance(stmt, (exp.Select, exp.With)):
        msg = "仅允许执行 SELECT 查询"
        raise ValueError(msg)
    return stmt
