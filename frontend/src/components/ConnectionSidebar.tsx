import { DeleteOutlined, EditOutlined, PlusOutlined } from "@ant-design/icons";
import { Button, Modal, Popconfirm, Typography, message } from "antd";
import { useState, type MouseEvent } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useDelete, useInvalidate, useList } from "@refinedev/core";
import { DatabaseForm } from "./DatabaseForm";
import { EditConnectionModal } from "./EditConnectionModal";
import type { DbConnectionRecord } from "../types/db";

export function ConnectionSidebar() {
  const { name: nameParam } = useParams<{ name?: string }>();
  const decoded = nameParam ? decodeURIComponent(nameParam) : "";
  const navigate = useNavigate();
  const invalidate = useInvalidate();
  const { data, isLoading } = useList<DbConnectionRecord>({ resource: "dbs" });
  const { mutate: removeConnection, isLoading: isDeleting } = useDelete();

  const rows = data?.data ?? [];
  const [addOpen, setAddOpen] = useState(false);
  const [editOpen, setEditOpen] = useState(false);
  const [editing, setEditing] = useState<DbConnectionRecord | null>(null);

  const select = (r: DbConnectionRecord) => {
    navigate(`/db/${encodeURIComponent(r.name)}`);
  };

  const confirmDelete = (r: DbConnectionRecord, e?: MouseEvent) => {
    e?.stopPropagation();
    removeConnection(
      { resource: "dbs", id: r.id },
      {
        onSuccess: () => {
          message.success("已删除连接");
          void invalidate({ resource: "dbs", invalidates: ["list"] });
          if (decoded === r.name) {
            const rest = rows.filter((x) => x.id !== r.id);
            if (rest.length > 0) {
              navigate(`/db/${encodeURIComponent(rest[0].name)}`, { replace: true });
            } else {
              navigate("/", { replace: true });
            }
          }
        },
      },
    );
  };

  return (
    <aside
      className="flex w-[260px] shrink-0 flex-col border-r-2 border-md-black bg-md-muted"
      data-testid="connection-sidebar"
    >
      <div className="border-b-2 border-[var(--color-border)] px-3 py-4">
        <Typography.Title level={5} className="!mb-1 !mt-0 !text-md-black">
          DB Query
        </Typography.Title>
        <Typography.Text type="secondary" className="text-xs">
          只读 SQL · PostgreSQL
        </Typography.Text>
      </div>

      <div className="flex shrink-0 flex-col gap-2 border-b-2 border-[var(--color-border)] p-3">
        <Button
          type="primary"
          block
          icon={<PlusOutlined />}
          onClick={() => setAddOpen(true)}
          data-testid="sidebar-add-db"
        >
          添加连接
        </Button>
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto px-2 py-2">
        <Typography.Text type="secondary" className="mb-2 block px-1 text-xs font-semibold uppercase tracking-wide">
          数据库
        </Typography.Text>
        {isLoading ? (
          <Typography.Text type="secondary" className="px-2 text-sm">
            加载中…
          </Typography.Text>
        ) : rows.length === 0 ? (
          <Typography.Text type="secondary" className="px-2 text-sm">
            暂无连接，请先添加。
          </Typography.Text>
        ) : (
          <ul className="flex flex-col gap-1">
            {rows.map((r) => {
              const active = decoded === r.name;
              return (
                <li key={r.id}>
                  <div
                    role="button"
                    tabIndex={0}
                    onClick={() => select(r)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" || e.key === " ") {
                        e.preventDefault();
                        select(r);
                      }
                    }}
                    className={`flex cursor-pointer items-center justify-between gap-1 rounded-[var(--radius-sm)] border-2 px-2 py-2 text-left transition-colors ${
                      active
                        ? "border-md-black bg-[rgba(255,241,0,0.45)]"
                        : "border-transparent hover:border-[var(--color-border-input)] hover:bg-[rgba(255,241,0,0.15)]"
                    }`}
                    data-testid={`sidebar-db-${r.name}`}
                  >
                    <span className="min-w-0 flex-1 truncate font-medium text-md-black">{r.name}</span>
                    <span className="flex shrink-0 gap-0" onClick={(e) => e.stopPropagation()}>
                      <Button
                        type="text"
                        size="small"
                        icon={<EditOutlined />}
                        className="!text-md-black"
                        aria-label={`编辑 ${r.name}`}
                        onClick={() => {
                          setEditing(r);
                          setEditOpen(true);
                        }}
                      />
                      <Popconfirm
                        title="删除此连接？"
                        description="元数据缓存将一并删除。"
                        okText="删除"
                        cancelText="取消"
                        okButtonProps={{ danger: true, loading: isDeleting }}
                        onConfirm={() => confirmDelete(r)}
                      >
                        <Button
                          type="text"
                          size="small"
                          danger
                          icon={<DeleteOutlined />}
                          aria-label={`删除 ${r.name}`}
                        />
                      </Popconfirm>
                    </span>
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </div>

      <Modal
        title="添加连接"
        open={addOpen}
        onCancel={() => setAddOpen(false)}
        footer={null}
        destroyOnClose
        width={520}
      >
        <div className="pt-2">
          <DatabaseForm
            onSuccess={(name) => {
              setAddOpen(false);
              navigate(`/db/${encodeURIComponent(name)}`);
            }}
          />
        </div>
      </Modal>

      <EditConnectionModal
        open={editOpen}
        record={editing}
        onClose={() => {
          setEditOpen(false);
          setEditing(null);
        }}
        onSaved={() => {
          setEditOpen(false);
          setEditing(null);
          void invalidate({ resource: "dbs", invalidates: ["list"] });
        }}
      />
    </aside>
  );
}
