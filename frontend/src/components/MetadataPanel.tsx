import { Button, Input, Spin, Tree, Typography } from "antd";
import type { TreeDataNode } from "antd/es/tree";
import { useCallback, useEffect, useMemo, useState } from "react";
import { DatabaseOutlined, ReloadOutlined } from "@ant-design/icons";
import { type TableInfo } from "../types/db";
import * as api from "../services/api";

function filterTables(tables: TableInfo[], kw: string): TableInfo[] {
  const k = kw.trim().toLowerCase();
  if (!k) {
    return tables;
  }
  return tables
    .map((t) => {
      const qualified = `${t.schemaName}.${t.tableName}`.toLowerCase();
      const cols = t.columns.filter(
        (c) =>
          c.name.toLowerCase().includes(k) || c.dataType.toLowerCase().includes(k),
      );
      if (qualified.includes(k) || t.tableType.toLowerCase().includes(k)) {
        return t;
      }
      if (cols.length > 0) {
        return { ...t, columns: cols };
      }
      return null;
    })
    .filter((x): x is TableInfo => x !== null);
}

function tablesToTreeData(tables: TableInfo[]): TreeDataNode[] {
  return tables.map((t) => {
    const q = `${t.schemaName}.${t.tableName}`;
    const key = `t:${q}`;
    return {
      title: `${q}`,
      key,
      children: t.columns.map((c) => ({
        title: `${c.name} · ${c.dataType}`,
        key: `c:${q}.${c.name}`,
        isLeaf: true,
      })),
    };
  });
}

export function MetadataPanel(props: {
  connectionName: string;
  /** 双击表名节点时插入示例 SQL */
  onInsertSnippet?: (sql: string) => void;
}) {
  const { connectionName, onInsertSnippet } = props;
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [tables, setTables] = useState<TableInfo[]>([]);
  const [cachedAt, setCachedAt] = useState<string | null>(null);
  const [keyword, setKeyword] = useState("");

  const load = useCallback(
    async (refresh: boolean) => {
      if (!connectionName) {
        return;
      }
      setError(null);
      if (refresh) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }
      try {
        const meta = await api.getMetadata(connectionName, refresh);
        setTables(meta.tables);
        setCachedAt(meta.cachedAt);
      } catch (e) {
        if (e instanceof api.ApiError) {
          setError(e.body.message);
        } else {
          setError("加载元数据失败");
        }
        setTables([]);
        setCachedAt(null);
      } finally {
        setLoading(false);
        setRefreshing(false);
      }
    },
    [connectionName],
  );

  useEffect(() => {
    void load(false);
  }, [load]);

  const filtered = useMemo(() => filterTables(tables, keyword), [tables, keyword]);

  const treeData = useMemo(() => tablesToTreeData(filtered), [filtered]);

  const titleRender = (node: TreeDataNode) => {
    const key = String(node.key);
    const label = typeof node.title === "string" ? node.title : String(node.title);
    return (
      <span
        onDoubleClick={(e) => {
          e.stopPropagation();
          if (!key.startsWith("t:") || !onInsertSnippet) {
            return;
          }
          const qualified = key.slice(2);
          const dot = qualified.indexOf(".");
          if (dot < 0) {
            return;
          }
          const schema = qualified.slice(0, dot);
          const table = qualified.slice(dot + 1);
          onInsertSnippet(`SELECT * FROM "${schema}"."${table}" LIMIT 100;`);
        }}
        className="cursor-default select-none"
      >
        {label}
      </span>
    );
  };

  if (loading && tables.length === 0) {
    return (
      <div className="flex flex-1 items-center justify-center py-16">
        <Spin size="large" />
      </div>
    );
  }

  return (
    <div className="flex h-full min-h-0 flex-col gap-3">
      <div className="flex items-center gap-2 border-b-2 border-[var(--color-border)] pb-3">
        <DatabaseOutlined className="text-lg text-[var(--color-text-secondary)]" />
        <Typography.Text strong className="text-[var(--color-black)]">
          Schema
        </Typography.Text>
      </div>
      <Input
        allowClear
        placeholder="搜索数据库、表…"
        value={keyword}
        onChange={(e) => setKeyword(e.target.value)}
        size="large"
        suffix={
          <Button
            type="text"
            size="small"
            icon={<ReloadOutlined spin={refreshing} />}
            onClick={() => void load(true)}
            aria-label="刷新元数据"
            className="!text-[var(--color-black)] hover:!bg-[rgba(255,241,0,0.35)]"
          />
        }
      />
      {cachedAt ? (
        <Typography.Text type="secondary" className="text-xs">
          缓存 {new Date(cachedAt).toLocaleString()}
        </Typography.Text>
      ) : null}
      {error ? (
        <Typography.Text type="danger" className="text-sm">
          {error}
        </Typography.Text>
      ) : null}
      <Typography.Text type="secondary" className="text-xs leading-snug">
        双击表名可插入 SELECT 模板
      </Typography.Text>
      <div className="min-h-0 flex-1 overflow-auto pr-1">
        {treeData.length === 0 ? (
          <Typography.Text type="secondary">暂无表或视图</Typography.Text>
        ) : (
          <Tree showLine blockNode defaultExpandAll treeData={treeData} titleRender={titleRender} />
        )}
      </div>
    </div>
  );
}
