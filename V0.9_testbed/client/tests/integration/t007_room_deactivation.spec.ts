import { expect, test } from "@playwright/test";
import { loginViaUi, logoutViaApi, uniqueName } from "./helpers";

// docs/P008-test-direction/T007-room-deactivation-removes-from-picker.md
test("T007: 会議室論理削除が予約作成画面の選択肢から除外される結合確認", async ({ page, context }) => {
  const roomName = uniqueName("T007会議室B");

  await loginViaUi(page, "admin001");
  await page.goto("/rooms");
  await page.getByLabel("会議室名").fill(roomName);
  await page.getByLabel("収容人数").fill("4");
  await page.getByRole("button", { name: "登録" }).click();
  await expect(page.getByText(roomName)).toBeVisible();

  page.once("dialog", (dialog) => dialog.accept());
  await page
    .locator("tr", { hasText: roomName })
    .getByRole("button", { name: "削除" })
    .click();
  await expect(page.getByText("無効").first()).toBeVisible();

  await logoutViaApi(context);
  await loginViaUi(page, "user001");
  await page.goto("/reservations/new");
  const roomSelect = page.getByLabel("会議室");
  await expect(roomSelect.locator("option", { hasText: roomName })).toHaveCount(0);

  await logoutViaApi(context);
  await loginViaUi(page, "admin001");
  await page.goto("/rooms");
  const row = page.locator("tr", { hasText: roomName });
  await expect(row.getByText("無効")).toBeVisible();
});
