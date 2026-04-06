import { expect, test } from "@playwright/test";

test("workspace shows connection sidebar", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByTestId("connection-sidebar")).toBeVisible({
    timeout: 30_000,
  });
});
