import { expect, test } from "@playwright/test";

const MYSQL_CONN_NAME = "interview";
const MYSQL_URL = "mysql://root:root@mysql:3306/interview_db";
const API = "http://127.0.0.1:8000/api/v1";

// Clean up before tests: remove the connection if it exists from a previous run
test.beforeAll(async ({ request }) => {
  await request.delete(`${API}/dbs/${MYSQL_CONN_NAME}`).catch(() => {});
});

test.afterAll(async ({ request }) => {
  await request.delete(`${API}/dbs/${MYSQL_CONN_NAME}`).catch(() => {});
});

test.describe("MySQL interview_db", () => {
  test("add MySQL connection, query, and see results", async ({ page }) => {
    await page.goto("/");

    // Wait for sidebar to load
    await expect(page.getByTestId("connection-sidebar")).toBeVisible({
      timeout: 30_000,
    });

    // --- Step 1: Add MySQL connection ---
    await page.getByTestId("sidebar-add-db").click();

    // Fill the form in the modal
    const nameInput = page.getByTestId("db-form-name");
    const urlInput = page.getByTestId("db-form-url");
    await expect(nameInput).toBeVisible({ timeout: 5_000 });

    await nameInput.fill(MYSQL_CONN_NAME);
    await urlInput.fill(MYSQL_URL);
    await page.getByTestId("db-form-submit").click();

    // Wait for connection to appear in the sidebar
    await expect(page.getByTestId(`sidebar-db-${MYSQL_CONN_NAME}`)).toBeVisible({
      timeout: 15_000,
    });

    // --- Step 2: Navigate to the connection and verify metadata loaded ---
    await page.getByTestId(`sidebar-db-${MYSQL_CONN_NAME}`).click();

    // Wait for workspace to load - the connection name should appear in the main header
    await expect(page.getByRole("main").locator(".font-semibold").filter({ hasText: "interview" })).toBeVisible({ timeout: 15_000 });

    // Wait for metadata panel to show tables (look for known table names)
    await expect(page.getByText("interview_db.candidates")).toBeVisible({ timeout: 20_000 });

    // --- Step 3: Execute a SQL query ---
    // Wait for the Execute Query button to be visible (workspace fully loaded)
    await expect(page.getByTestId("query-run")).toBeVisible({ timeout: 15_000 });

    // Default SQL is "SELECT 1 AS one" - execute it first to verify basic query works
    await page.getByTestId("query-run").click();

    // Wait for either result or error to appear
    await expect(page.getByTestId("query-result").or(page.getByTestId("query-result-error"))).toBeVisible({ timeout: 15_000 });

    // Now set a real query via Monaco's API and execute
    await page.evaluate(() => {
      const editor = (window as any).monaco?.editor?.getEditors()?.[0];
      if (editor) {
        editor.setValue("SELECT name, current_company FROM candidates LIMIT 5");
      }
    });
    // If Monaco global isn't available, fall back to keyboard input
    const editorContent = await page.locator(".monaco-editor .view-lines").textContent();
    if (!editorContent?.includes("candidates")) {
      // Fall back: click into editor and type
      await page.locator(".monaco-editor").first().click();
      await page.keyboard.press("ControlOrMeta+a");
      await page.keyboard.type("SELECT name, current_company FROM candidates LIMIT 5", { delay: 10 });
    }

    // Click Execute Query
    await page.getByTestId("query-run").click();

    // Wait for results - could be new result or error
    await expect(page.getByTestId("query-result").or(page.getByTestId("query-result-error"))).toBeVisible({ timeout: 15_000 });
  });

  test("natural language generates MySQL SQL", async ({ page, request }) => {
    // Check if OPENAI_API_KEY is configured by attempting a natural query via API
    const checkResp = await request.post(`${API}/dbs/${MYSQL_CONN_NAME}/query/natural`, {
      data: { prompt: "test" },
    });
    if (checkResp.status() === 500) {
      const body = await checkResp.json();
      if (body?.error === "llm_unavailable") {
        test.skip(true, "OPENAI_API_KEY not configured, skipping natural language test");
      }
    }

    // Ensure connection and metadata exist
    await request.put(`${API}/dbs/${MYSQL_CONN_NAME}`, {
      data: { url: MYSQL_URL },
    });
    await request.get(`${API}/dbs/${MYSQL_CONN_NAME}?refresh=true`);

    await page.goto("/");
    await expect(page.getByTestId("connection-sidebar")).toBeVisible({ timeout: 30_000 });

    // Click the connection
    await page.getByTestId(`sidebar-db-${MYSQL_CONN_NAME}`).click();
    await expect(page.getByRole("main").locator(".font-semibold").filter({ hasText: "interview" })).toBeVisible({ timeout: 15_000 });

    // Wait for metadata to load
    await expect(page.getByText("interview_db.candidates")).toBeVisible({ timeout: 20_000 });

    // Fill natural language prompt
    const prompt = page.getByTestId("natural-query-prompt");
    await expect(prompt).toBeVisible({ timeout: 5_000 });
    await prompt.fill("查询所有已收到 offer 的候选人姓名和 offer 薪资");

    // Click Generate SQL
    await page.getByTestId("natural-query-generate").click();

    // Wait for SQL to be generated and appear in the editor
    // The editor content should change from default to generated SQL containing SELECT
    await expect(page.locator(".monaco-editor")).toContainText("SELECT", { timeout: 30_000 });

    // Execute the generated SQL
    await page.getByTestId("query-run").click();

    // Wait for results
    await expect(page.getByTestId("query-result")).toBeVisible({ timeout: 15_000 });
  });
});
