import type { DataProvider } from "@refinedev/core";
import * as api from "../services/api";
import type { DbConnectionRecord } from "../types/db";

const notImplemented = (): never => {
  throw new Error("Not implemented");
};

export const dataProvider: DataProvider = {
  getApiUrl: () => import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000",

  getList: async ({ resource }) => {
    if (resource === "dbs") {
      const rows = await api.listDbs();
      const data: DbConnectionRecord[] = rows.map((r) => ({
        ...r,
        id: r.name,
      }));
      return { data, total: data.length };
    }
    throw new Error(`Unknown resource: ${resource}`);
  },

  getOne: async () => notImplemented(),
  create: async () => notImplemented(),
  update: async () => notImplemented(),
  deleteOne: async ({ resource, id }) => {
    if (resource === "dbs") {
      const sid = String(id);
      await api.deleteDb(sid);
      return {
        data: { id: sid, name: sid, url: "", createdAt: "", updatedAt: "" } as DbConnectionRecord,
      };
    }
    throw new Error(`Unknown resource: ${resource}`);
  },
};
