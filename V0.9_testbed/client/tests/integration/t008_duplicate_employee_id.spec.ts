import { expect, test } from "@playwright/test";
import { loginViaUi } from "./helpers";

// docs/P008-test-direction/T008-duplicate-employee-id.md
test("T008: 社員ID重複登録エラーの結合確認", async ({ page, context }) => {
  await loginViaUi(page, "admin001");
  await page.goto("/users");

  const beforeCount = (await (await context.request.get("/api/users")).json()).length;

  await page.getByLabel("社員ID").fill("user001"); // 既存の社員ID
  await page.getByLabel("氏名").fill("重複テスト");
  await page.getByLabel("初期パスワード").fill("Passw0rd1");
  await page.getByRole("button", { name: "登録" }).click();

  await expect(page.getByRole("alert")).toHaveText("この社員IDは既に登録されています");

  const afterCount = (await (await context.request.get("/api/users")).json()).length;
  expect(afterCount).toBe(beforeCount);
});
