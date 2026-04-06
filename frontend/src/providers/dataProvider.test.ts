import { beforeEach, describe, expect, it, vi } from "vitest";

import type { DbConnection } from "../types/db";
import { dataProvider } from "./dataProvider";

const { listDbs, deleteDb } = vi.hoisted(() => ({
  listDbs: vi.fn(),
  deleteDb: vi.fn(),
}));

vi.mock("../services/api", () => ({
  listDbs,
  deleteDb,
}));

describe("dataProvider", () => {
  beforeEach(() => {
    listDbs.mockReset();
  });

  it("getList maps dbs to id = name", async () => {
    const rows: DbConnection[] = [
      {
        name: "pg",
        url: "postgresql://u:p@h:5432/db",
        createdAt: "2024-01-01T00:00:00Z",
        updatedAt: "2024-01-01T00:00:00Z",
      },
    ];
    listDbs.mockResolvedValue(rows);

    const res = await dataProvider.getList!({ resource: "dbs" } as never);

    expect(res.total).toBe(1);
    expect(res.data[0].id).toBe("pg");
    expect(res.data[0].name).toBe("pg");
  });

  it("getList throws for unknown resource", async () => {
    await expect(
      dataProvider.getList!({ resource: "other" } as never),
    ).rejects.toThrow("Unknown resource");
  });
});
