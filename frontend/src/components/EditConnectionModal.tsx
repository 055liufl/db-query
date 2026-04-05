import { Form, Input, Modal, message } from "antd";
import { useEffect } from "react";
import * as api from "../services/api";
import type { DbConnectionRecord } from "../types/db";

export function EditConnectionModal(props: {
  open: boolean;
  record: DbConnectionRecord | null;
  onClose: () => void;
  onSaved: () => void;
}) {
  const { open, record, onClose, onSaved } = props;
  const [form] = Form.useForm<{ name: string; url: string }>();

  useEffect(() => {
    if (open && record) {
      form.setFieldsValue({ name: record.name, url: record.url });
    }
  }, [open, record, form]);

  const handleOk = async () => {
    if (!record) {
      return;
    }
    try {
      const v = await form.validateFields();
      await api.putDb(record.name, v.url.trim());
      message.success("连接已更新");
      onClose();
      onSaved();
    } catch (e) {
      if (e instanceof api.ApiError) {
        const d = e.body.detail?.trim();
        const extra =
          d && d.length > 0
            ? ` ${d.length > 180 ? `${d.slice(0, 180)}…` : d}`
            : "";
        message.error(`${e.body.message}${extra}`);
      }
    }
  };

  return (
    <Modal
      title="编辑连接"
      open={open}
      onCancel={onClose}
      onOk={() => void handleOk()}
      okText="保存"
      destroyOnClose
      afterClose={() => form.resetFields()}
    >
      <Form form={form} layout="vertical" className="mt-2">
        <Form.Item label="连接名称" name="name">
          <Input disabled />
        </Form.Item>
        <Form.Item
          label="数据库 URL"
          name="url"
          rules={[{ required: true, message: "请输入连接 URL" }]}
        >
          <Input placeholder="postgresql://…" size="large" autoComplete="off" />
        </Form.Item>
      </Form>
    </Modal>
  );
}
