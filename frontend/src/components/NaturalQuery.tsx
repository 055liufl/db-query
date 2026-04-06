import { ThunderboltOutlined } from "@ant-design/icons";
import { Alert, Button, Input, Typography } from "antd";
import { useEffect, useState } from "react";
import * as api from "../services/api";

type NaturalQueryProps = {
  connectionName: string;
  onSqlGenerated: (sql: string) => void;
};

export function NaturalQuery({ connectionName, onSqlGenerated }: NaturalQueryProps) {
  const [prompt, setPrompt] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setPrompt("");
    setError(null);
    setLoading(false);
  }, [connectionName]);

  const generate = async () => {
    const p = prompt.trim();
    if (!p) {
      setError("请输入自然语言描述");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const r = await api.naturalQuery(connectionName, { prompt: p });
      onSqlGenerated(r.generatedSql);
    } catch (e) {
      if (e instanceof api.ApiError) {
        const d = e.body.detail?.trim();
        const extra =
          d && d.length > 0
            ? ` ${d.length > 180 ? `${d.slice(0, 180)}…` : d}`
            : "";
        setError(`${e.body.message}${extra}`);
      } else {
        const msg = e instanceof Error ? e.message : "";
        const looksLikeNetwork =
          msg === "Failed to fetch" ||
          /networkerror|load failed|failed to fetch/i.test(msg);
        if (looksLikeNetwork && typeof window !== "undefined") {
          const host = `${window.location.hostname}:8000`;
          setError(
            `无法连接后端 API（应对 ${host} 可访问）。请确认 backend 容器已运行、端口 8000 已映射，并尝试打开 ${window.location.protocol}//${host}/docs 查看接口文档。`,
          );
        } else if (e instanceof Error) {
          setError(`生成失败：${e.message}`);
        } else {
          setError("生成失败");
        }
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col gap-2 border-b border-[var(--color-border)] bg-[var(--color-bg-muted)] px-4 py-3 md:px-8">
      <Typography.Text type="secondary" className="text-xs font-semibold uppercase tracking-wide">
        自然语言
      </Typography.Text>
      {error ? (
        <Alert type="error" message={error} showIcon closable onClose={() => setError(null)} />
      ) : null}
      <Input.TextArea
        data-testid="natural-query-prompt"
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        placeholder="用中文或英文描述想查的数据，例如：查询所有用户的邮箱"
        rows={2}
        maxLength={2000}
        disabled={loading}
        className="!resize-y !rounded-[var(--radius-sm)] !border-2 !border-[var(--color-border-input)]"
      />
      <Button
        type="primary"
        icon={<ThunderboltOutlined />}
        loading={loading}
        onClick={() => void generate()}
        data-testid="natural-query-generate"
        className="w-fit"
      >
        生成 SQL
      </Button>
    </div>
  );
}
