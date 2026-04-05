/** API 响应（camelCase），与 specs/001-db-query-tool/contracts/api.md 一致 */

export interface DbConnection {
  name: string;
  url: string;
  createdAt: string;
  updatedAt: string;
}

/** Refine BaseRecord 需要 `id`，与 `name` 相同 */
export type DbConnectionRecord = DbConnection & { id: string };

export interface ColumnInfo {
  name: string;
  dataType: string;
  isNullable: boolean;
  columnDefault: string | null;
}

export interface TableInfo {
  schemaName: string;
  tableName: string;
  tableType: string;
  columns: ColumnInfo[];
}

export interface DbMetadata {
  connectionName: string;
  tables: TableInfo[];
  cachedAt: string;
}
