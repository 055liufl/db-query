import { Button, Form, Input, message } from "antd";
import { useInvalidate } from "@refinedev/core";
import * as api from "../services/api";

type DatabaseFormProps = {
  /** 保存成功且列表已 invalidate 后调用（用于侧栏弹窗内跳转） */
  onSuccess?: (name: string) => void;
};

export function DatabaseForm({ onSuccess }: DatabaseFormProps) {
  const invalidate = useInvalidate();
  const [form] = Form.useForm<{ name: string; url: string }>();

  const onFinish = async (values: { name: string; url: string }) => {
    const name = values.name.trim();
    try {
      await api.putDb(name, values.url.trim());
      message.success("连接已保存");
      form.resetFields();
      await invalidate({ resource: "dbs", invalidates: ["list"] });
      onSuccess?.(name);
    } catch (e) {
      if (e instanceof api.ApiError) {
        const d = e.body.detail?.trim();
        const extra =
          d && d.length > 0
            ? ` ${d.length > 180 ? `${d.slice(0, 180)}…` : d}`
            : "";
        message.error(`${e.body.message}${extra}`);
      } else {
        message.error("请求失败");
      }
    }
  };

  return (
    <Form
      form={form}
      layout="vertical"
      onFinish={onFinish}
      className="max-w-xl"
    >
      <Form.Item
        label="连接名称"
        name="name"
        rules={[
          { required: true, message: "请输入连接名称" },
          {
            pattern: /^[a-zA-Z0-9_-]{1,64}$/,
            message: "仅允许字母、数字、连字符、下划线，长度 1~64",
          },
        ]}
      >
        <Input
          placeholder="例如 my-postgres 或 my-mysql"
          data-testid="db-form-name"
          size="large"
          autoComplete="off"
        />
      </Form.Item>
      <Form.Item label="数据库 URL" name="url" rules={[{ required: true, message: "请输入连接 URL" }]}>
        <Input
          placeholder="postgres://user:pass@host:5432/db 或 mysql://user:pass@host:3306/db"
          data-testid="db-form-url"
          size="large"
          autoComplete="off"
        />
      </Form.Item>
      <Form.Item className="!mb-0">
        <Button type="primary" htmlType="submit" data-testid="db-form-submit" size="large">
          保存连接
        </Button>
      </Form.Item>
    </Form>
  );
}
