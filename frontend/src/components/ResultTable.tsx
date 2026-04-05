import {
  Alert,
  Button,
  Checkbox,
  Input,
  Popover,
  Space,
  Spin,
  Table,
  Typography,
} from "antd";
import type { ColumnsType } from "antd/es/table";
import { useCallback, useMemo, useState } from "react";
import {
  DownloadOutlined,
  FilterOutlined,
  LineChartOutlined,
  TableOutlined,
} from "@ant-design/icons";
import type { QueryColumn, QueryResult } from "../types/query";

function escapeCsvCell(v: unknown): string {
  if (v === null || v === undefined) {
    return "";
  }
  const s = typeof v === "object" ? JSON.stringify(v) : String(v);
  if (/[",\n\r]/.test(s)) {
    return `"${s.replace(/"/g, '""')}"`;
  }
  return s;
}

function exportCsv(columns: QueryColumn[], rows: Record<string, unknown>[]): string {
  const header = columns.map((c) => escapeCsvCell(c.name)).join(",");
  const lines = rows.map((row) =>
    columns.map((c) => escapeCsvCell(row[c.name])).join(","),
  );
  return [header, ...lines].join("\r\n");
}

function downloadText(filename: string, content: string, mime: string) {
  const blob = new Blob([content], { type: mime });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

function compareValues(a: unknown, b: unknown): number {
  if (a === b) {
    return 0;
  }
  if (a == null) {
    return -1;
  }
  if (b == null) {
    return 1;
  }
  if (typeof a === "number" && typeof b === "number") {
    return a - b;
  }
  return String(a).localeCompare(String(b), undefined, { numeric: true });
}

type RowWithKey = Record<string, unknown> & { __rk: string };

export function ResultTable(props: {
  loading: boolean;
  result: QueryResult | null;
  error: string | null;
}) {
  const { loading, result, error } = props;
  const [filterText, setFilterText] = useState("");
  const [hiddenCols, setHiddenCols] = useState<Record<string, boolean>>({});

  const resetColumnVisibility = useCallback(() => {
    setHiddenCols({});
  }, []);

  const baseRows = useMemo(() => result?.rows ?? [], [result]);

  const filteredRows = useMemo(() => {
    if (!result) {
      return [];
    }
    const f = filterText.trim().toLowerCase();
    if (!f) {
      return baseRows;
    }
    return baseRows.filter((row) =>
      result.columns.some((c) =>
        String(row[c.name] ?? "")
          .toLowerCase()
          .includes(f),
      ),
    );
  }, [baseRows, filterText, result]);

  const dataSource: RowWithKey[] = useMemo(
    () => filteredRows.map((r, i) => ({ ...r, __rk: `row-${i}` })),
    [filteredRows],
  );

  const columnPicker = useMemo(() => {
    if (!result) {
      return null;
    }
    return (
      <Space direction="vertical" size={4} className="max-h-72 overflow-auto py-1">
        {result.columns.map((c) => (
          <Checkbox
            key={c.name}
            checked={!hiddenCols[c.name]}
            onChange={(e) => {
              setHiddenCols((prev) => ({
                ...prev,
                [c.name]: !e.target.checked,
              }));
            }}
          >
            {c.name}
          </Checkbox>
        ))}
      </Space>
    );
  }, [result, hiddenCols]);

  if (error) {
    return <Alert type="error" message={error} showIcon data-testid="query-result-error" />;
  }

  if (loading && !result) {
    return (
      <div
        className="flex flex-1 items-center justify-center py-24"
        data-testid="query-result-loading"
      >
        <Spin size="large" />
      </div>
    );
  }

  if (!result && !loading) {
    return (
      <div
        className="flex flex-1 flex-col items-center justify-center gap-3 rounded-[var(--radius-md)] border-2 border-dashed border-[var(--color-border)] bg-[var(--color-bg-muted)] py-16 md-enter"
        data-testid="query-result-empty"
      >
        <TableOutlined className="text-4xl text-[var(--color-text-secondary)]" />
        <Typography.Text type="secondary" className="text-center text-base">
          点击 <strong className="text-[var(--color-black)]">Execute Query</strong>{" "}
          运行 SQL，结果将出现在此区域
        </Typography.Text>
      </div>
    );
  }

  const columns: ColumnsType<RowWithKey> =
    result?.columns
      .filter((c) => !hiddenCols[c.name])
      .map((c) => ({
        title: `${c.name} (${c.dataType})`,
        dataIndex: c.name,
        key: c.name,
        ellipsis: true,
        sorter: (a, b) => compareValues(a[c.name], b[c.name]),
        render: (v: unknown) => {
          if (v === null || v === undefined) {
            return <Typography.Text type="secondary">NULL</Typography.Text>;
          }
          if (typeof v === "object") {
            return JSON.stringify(v);
          }
          return String(v);
        },
      })) ?? [];

  return (
    <div className="flex min-h-0 flex-1 flex-col gap-0" data-testid="query-result">
      {result?.truncated ? (
        <Alert
          type="warning"
          showIcon
          message="结果可能因服务端默认 LIMIT 1000 被截断"
          className="mb-2 shrink-0"
        />
      ) : null}

      <div className="md-toolbar md-result-toolbar mb-3 flex shrink-0 flex-wrap items-center justify-between gap-3 pb-3">
        <Typography.Text className="font-medium text-[var(--color-text-secondary)]">
          {result
            ? filterText.trim()
              ? `显示 ${filteredRows.length} / ${result.rowCount} 行 · ${result.elapsedMs} ms`
              : `${result.rowCount} 行 · ${result.elapsedMs} ms`
            : ""}
        </Typography.Text>
        <Space wrap size="small">
          <Input
            allowClear
            prefix={<FilterOutlined className="text-[var(--color-text-secondary)]" />}
            placeholder="筛选结果…"
            value={filterText}
            onChange={(e) => setFilterText(e.target.value)}
            style={{ width: 220 }}
            disabled={!result}
            size="middle"
          />
          <Button
            icon={<LineChartOutlined />}
            disabled
            title="可视化（暂未实现）"
          >
            Visualize
          </Button>
          <Popover trigger="click" placement="bottomRight" title="显示列" content={columnPicker}>
            <Button icon={<TableOutlined />} disabled={!result}>
              Columns
            </Button>
          </Popover>
          <Button
            icon={<DownloadOutlined />}
            disabled={!result}
            onClick={() => {
              if (!result) {
                return;
              }
              downloadText(
                "query-result.csv",
                exportCsv(result.columns, baseRows),
                "text/csv;charset=utf-8",
              );
            }}
          >
            Export CSV
          </Button>
          <Button
            disabled={!result}
            onClick={() => {
              if (!result) {
                return;
              }
              downloadText(
                "query-result.json",
                `${JSON.stringify({ sql: result.sql, rows: baseRows }, null, 2)}\n`,
                "application/json",
              );
            }}
          >
            Export JSON
          </Button>
        </Space>
      </div>

      <div className="relative min-h-0 flex-1 overflow-hidden">
        {result ? (
          <Table<RowWithKey>
            size="small"
            rowKey="__rk"
            dataSource={dataSource}
            columns={columns}
            pagination={{
              pageSize: 50,
              showSizeChanger: true,
              showTotal: (total) => `共 ${total} 条`,
            }}
            scroll={{ x: "max-content", y: "calc(100vh - 380px)" }}
            locale={{ emptyText: "无匹配行" }}
            className="query-result-table"
          />
        ) : null}
      </div>

      {result && Object.values(hiddenCols).some(Boolean) ? (
        <Button type="link" size="small" className="self-start" onClick={resetColumnVisibility}>
          显示全部列
        </Button>
      ) : null}
    </div>
  );
}
