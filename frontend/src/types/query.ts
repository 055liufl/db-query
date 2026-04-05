/** 查询 API 类型，与 contracts/api.md 一致 */

export interface QueryRequest {
  sql: string;
}

export interface QueryColumn {
  name: string;
  dataType: string;
}

export interface QueryResult {
  sql: string;
  columns: QueryColumn[];
  rows: Record<string, unknown>[];
  rowCount: number;
  truncated: boolean;
  elapsedMs: number;
}

/** 后端错误体（扁平 JSON，非 FastAPI 默认 detail 包裹） */
export interface ApiErrorBody {
  error: string;
  message: string;
  detail?: string | null;
}
