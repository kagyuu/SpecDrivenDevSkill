import { expect, test } from "@playwright/test";
import { createRoomViaApi, loginViaApi, loginViaUi, logoutViaApi, todayDateString, uniqueName } from "../integration/helpers";

// docs/P009-acceptance-direction/A001-general-user-journey.md
test("A001: 一般ユーザーの標準的な業務フロー", async ({ page, context }) => {
  await loginViaApi(context, "admin001");
  const roomA = await createRoomViaApi(context, uniqueName("A001会議室A"), 10);
  await logoutViaApi(context);

  const date = todayDateString(0);

  // 1. ログイン
  await loginViaUi(page, "user001");

  // 2. S02で空きセルをクリックしてS03へ
  await page.goto(`/reservations/new?room_id=${roomA.id}&date=${date}`);

  // 3. S03で登録
  await page.getByLabel("会議室").selectOption(String(roomA.id));
  await page.getByLabel("日付").fill(date);
  await page.getByLabel("開始時刻").fill("14:00");
  await page.getByLabel("終了時刻").fill("15:00");
  await page.getByLabel("件名").fill("定例MTG");
  await page.getByLabel("参加予定人数").fill("3");
  await page.getByRole("button", { name: "登録" }).click();
  await page.waitForURL("**/calendar");

  // 4. S02で該当セルに表示されることを確認(14:00-15:00は2コマにまたがるため、
  //    同じ表示テキストのセルが2つ存在するのが正しい挙動。.first()で1つ目の存在を確認する)
  await page.getByRole("button", { name: date }).click();
  await expect(page.getByText("一般花子 / 定例MTG").first()).toBeVisible();

  // 5. マイ予約一覧(S05)で表示確認
  await page.goto("/my-reservations");
  await expect(page.getByText("定例MTG")).toBeVisible();

  // 6. S04を開き件名変更・更新
  await page.getByRole("button", { name: date }).click();
  await expect(page.getByLabel("件名")).toHaveValue("定例MTG");
  await page.getByLabel("件名").fill("定例MTG(会議室変更前)");
  await page.getByRole("button", { name: "更新" }).click();
  await page.waitForURL("**/calendar");

  // 7. 再度S04を開き取消
  await page.goto("/my-reservations");
  await page.getByRole("button", { name: date }).click();
  page.once("dialog", (dialog) => dialog.accept());
  await page.getByRole("button", { name: "取消" }).click();
  await page.waitForURL("**/calendar");

  // 8. S02のセルが空きに戻っていること
  await page.getByRole("button", { name: date }).click();
  await expect(page.getByText("定例MTG(会議室変更前)")).toHaveCount(0);

  // 9. ログアウトしS01へ戻ること(UI上のログアウト導線を実際に操作する)
  await page.goto("/calendar");
  await page.getByRole("button", { name: "ログアウト" }).click();
  await expect(page.getByLabel("社員ID")).toBeVisible();
});
