import type { DbConnection, DbMetadata } from "../types/db";
import type {
  ApiErrorBody,
  NaturalQueryRequest,
  NaturalQueryResult,
  QueryRequest,
  QueryResult,
} from "../types/query";

export function apiRoot(): string {
  const fromEnv = import.meta.env.VITE_API_BASE_URL?.trim();
  if (fromEnv) {
    return fromEnv.replace(/\/$/, "");
  }
  // Browser: call API on same host as the page (port 8000). Fixes Docker Toolbox / LAN
  // when the UI is opened as http://<vm-ip>:3000 but localhost:8000 is not reachable.
  if (typeof window !== "undefined") {
    const { protocol, hostname } = window.location;
    return `${protocol}//${hostname}:8000`;
  }
  return "http://127.0.0.1:8000";
}

function apiV1(): string {
  return `${apiRoot()}/api/v1`;
}

export class ApiError extends Error {
  readonly status: number;

  readonly body: ApiErrorBody;

  constructor(status: number, body: ApiErrorBody) {
    super(body.message);
    this.name = "ApiError";
    this.status = status;
    this.body = body;
  }
}

function throwFromErrorText(status: number, text: string): never {
  try {
    const data = JSON.parse(text) as ApiErrorBody;
    if (data.error && data.message) {
      throw new ApiError(status, data);
    }
  } catch (e) {
    if (e instanceof ApiError) {
      throw e;
    }
  }
  throw new ApiError(status, {
    error: "unknown",
    message: text || "请求失败",
    detail: null,
  });
}

async function readError(res: Response): Promise<never> {
  const text = await res.text();
  throwFromErrorText(res.status, text);
}

export async function listDbs(): Promise<DbConnection[]> {
  const res = await fetch(`${apiV1()}/dbs`);
  if (!res.ok) {
    await readError(res);
  }
  return (await res.json()) as DbConnection[];
}

export async function putDb(name: string, url: string): Promise<DbConnection> {
  const res = await fetch(`${apiV1()}/dbs/${encodeURIComponent(name)}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url } satisfies { url: string }),
  });
  if (!res.ok) {
    await readError(res);
  }
  return (await res.json()) as DbConnection;
}

export async function deleteDb(name: string): Promise<void> {
  const res = await fetch(`${apiV1()}/dbs/${encodeURIComponent(name)}`, {
    method: "DELETE",
  });
  if (!res.ok) {
    await readError(res);
  }
}

export async function getMetadata(name: string, refresh: boolean): Promise<DbMetadata> {
  const q = refresh ? "?refresh=true" : "";
  const res = await fetch(`${apiV1()}/dbs/${encodeURIComponent(name)}${q}`);
  if (!res.ok) {
    await readError(res);
  }
  return (await res.json()) as DbMetadata;
}

export async function naturalQuery(
  name: string,
  body: NaturalQueryRequest,
): Promise<NaturalQueryResult> {
  const res = await fetch(`${apiV1()}/dbs/${encodeURIComponent(name)}/query/natural`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const text = await res.text();
  if (!res.ok) {
    throwFromErrorText(res.status, text);
  }
  try {
    return JSON.parse(text) as NaturalQueryResult;
  } catch {
    throw new ApiError(res.status, {
      error: "invalid_response",
      message: "响应不是合法 JSON",
      detail: text.length > 400 ? `${text.slice(0, 400)}…` : text,
    });
  }
}

export async function runQuery(name: string, body: QueryRequest): Promise<QueryResult> {
  const res = await fetch(`${apiV1()}/dbs/${encodeURIComponent(name)}/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const text = await res.text();
  if (!res.ok) {
    throwFromErrorText(res.status, text);
  }
  try {
    return JSON.parse(text) as QueryResult;
  } catch {
    throw new ApiError(res.status, {
      error: "invalid_response",
      message: "响应不是合法 JSON",
      detail: text.length > 400 ? `${text.slice(0, 400)}…` : text,
    });
  }
}
