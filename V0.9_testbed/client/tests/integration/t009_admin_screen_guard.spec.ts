import { expect, test } from "@playwright/test";
import { loginViaUi } from "./helpers";

// docs/P008-test-direction/T009-admin-screen-guard.md
test("T009: 管理者専用画面への一般ユーザーアクセス時のフロント+APIガード結合確認", async ({ page, context }) => {
  await loginViaUi(page, "user001");

  await page.goto("/rooms");
  await expect(page.getByText("この画面を表示する権限がありません。")).toBeVisible();
  await expect(page.getByLabel("会議室名")).toHaveCount(0);

  await page.goto("/users");
  await expect(page.getByText("この画面を表示する権限がありません。")).toBeVisible();
  await expect(page.getByLabel("社員ID")).toHaveCount(0);

  const roomsResp = await context.request.get("/api/rooms", { params: { include_inactive: "true" } });
  expect(roomsResp.status()).toBe(200); // 一般ユーザーはinclude_inactiveを無視されるだけで200

  const usersResp = await context.request.get("/api/users");
  expect(usersResp.status()).toBe(403);
  expect((await usersResp.json()).error_code).toBe("FORBIDDEN");
});
