import { PlayCircleOutlined, TableOutlined } from "@ant-design/icons";
import { Button, Typography } from "antd";
import { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useList } from "@refinedev/core";
import { ConnectionSidebar } from "../components/ConnectionSidebar";
import { MetadataPanel } from "../components/MetadataPanel";
import { ResultTable } from "../components/ResultTable";
import { SqlEditor } from "../components/SqlEditor";
import * as api from "../services/api";
import type { DbConnectionRecord } from "../types/db";
import type { QueryResult } from "../types/query";

export function WorkspacePage() {
  const { name: nameParam } = useParams<{ name?: string }>();
  const navigate = useNavigate();
  const { data, isLoading } = useList<DbConnectionRecord>({ resource: "dbs" });
  const rawRows = data?.data;
  const decoded = nameParam ? decodeURIComponent(nameParam) : "";

  useEffect(() => {
    if (isLoading) {
      return;
    }
    const rows = rawRows ?? [];
    if (rows.length === 0) {
      return;
    }
    if (!nameParam) {
      navigate(`/db/${encodeURIComponent(rows[0].name)}`, { replace: true });
      return;
    }
    const exists = rows.some((r) => r.name === decoded);
    if (!exists) {
      navigate(`/db/${encodeURIComponent(rows[0].name)}`, { replace: true });
    }
  }, [isLoading, nameParam, decoded, navigate, rawRows]);

  const [sql, setSql] = useState("SELECT 1 AS one");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<QueryResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setSql("SELECT 1 AS one");
    setResult(null);
    setError(null);
  }, [decoded]);

  const tabTime = useMemo(() => new Date().toLocaleTimeString(), []);

  const run = async () => {
    if (!decoded) {
      return;
    }
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const r = await api.runQuery(decoded, { sql });
      setResult(r);
    } catch (e) {
      if (e instanceof api.ApiError) {
        const d = e.body.detail?.trim();
        const extra =
          d && d.length > 0
            ? ` ${d.length > 180 ? `${d.slice(0, 180)}…` : d}`
            : "";
        setError(`${e.body.message}${extra}`);
      } else if (e instanceof Error) {
        setError(`执行失败：${e.message}`);
      } else {
        setError("执行失败");
      }
    } finally {
      setLoading(false);
    }
  };

  const rows = rawRows ?? [];
  const showQuery = decoded.length > 0 && rows.some((r) => r.name === decoded);

  return (
    <div className="flex h-screen flex-col overflow-hidden bg-[var(--color-bg-page)] text-[var(--color-text)] md:flex-row">
      <ConnectionSidebar />

      <div className="flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden">
        {isLoading && rows.length === 0 ? (
          <div className="flex flex-1 items-center justify-center p-8">
            <Typography.Text type="secondary">加载中…</Typography.Text>
          </div>
        ) : rows.length === 0 ? (
          <div className="flex flex-1 flex-col items-center justify-center gap-4 p-8 text-center">
            <Typography.Title level={4} className="!mb-0 !text-md-black">
              暂无数据库连接
            </Typography.Title>
            <Typography.Text type="secondary" className="max-w-md">
              在左侧点击「添加连接」保存 PostgreSQL 连接后即可浏览元数据并执行只读查询。
            </Typography.Text>
          </div>
        ) : !showQuery ? (
          <div className="flex flex-1 items-center justify-center p-8">
            <Typography.Text type="secondary">正在打开连接…</Typography.Text>
          </div>
        ) : (
          <div className="flex min-h-0 flex-1 flex-col overflow-hidden md:flex-row">
            <aside className="flex w-sidebar shrink-0 flex-col overflow-hidden border-b-2 border-md-border bg-md-muted px-4 py-4 md:border-b-0 md:border-r-2">
              <MetadataPanel connectionName={decoded} onInsertSnippet={setSql} />
            </aside>

            <main className="grid min-h-0 min-w-0 flex-1 grid-rows-[auto_auto_minmax(260px,38vh)_1fr] bg-[var(--color-bg)]">
              <div className="flex shrink-0 items-center justify-between gap-4 border-b-2 border-[var(--color-border)] px-4 py-3 md:px-8">
                <div className="flex min-w-0 items-center gap-3 text-[var(--color-text)]">
                  <TableOutlined className="shrink-0 text-xl text-[var(--color-text-secondary)]" />
                  <span className="truncate font-semibold">{decoded}</span>
                </div>
                <Button
                  type="primary"
                  icon={<PlayCircleOutlined />}
                  data-testid="query-run"
                  onClick={() => void run()}
                  loading={loading}
                  size="large"
                >
                  Execute Query
                </Button>
              </div>

              <div className="flex shrink-0 items-center border-b border-[var(--color-border)] bg-[var(--color-bg-muted)] px-4 py-2 text-xs font-medium text-[var(--color-text-secondary)] md:px-8">
                <span className="rounded-md border border-[var(--color-border-input)] bg-[var(--color-bg)] px-2 py-0.5 font-mono text-[var(--color-black)]">
                  Query · {tabTime}
                </span>
              </div>

              <div className="min-h-0 border-b-2 border-[var(--color-border)] bg-[var(--color-bg)] px-4 pb-6 pt-3 md:px-8 md:pb-7">
                <div className="md-editor-frame">
                  <SqlEditor value={sql} onChange={setSql} height="360px" theme="vs-dark" />
                </div>
              </div>

              <section className="flex min-h-0 flex-col overflow-hidden bg-[var(--color-bg-muted)] px-4 pb-4 pt-8 md:px-8 md:pb-5 md:pt-10">
                <Typography.Title
                  level={5}
                  className="!mb-4 !mt-0 border-l-4 border-md-primary pl-3 !font-bold !text-[var(--color-black)]"
                >
                  结果
                </Typography.Title>
                <div className="min-h-0 flex-1 overflow-hidden">
                  <ResultTable loading={loading} result={result} error={error} />
                </div>
              </section>
            </main>
          </div>
        )}
      </div>
    </div>
  );
}
