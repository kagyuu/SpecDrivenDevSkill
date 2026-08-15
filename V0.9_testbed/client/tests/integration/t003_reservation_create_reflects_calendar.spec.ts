import { expect, test } from "@playwright/test";
import { createRoomViaApi, loginViaApi, loginViaUi, logoutViaApi, todayDateString, uniqueName } from "./helpers";

// docs/P008-test-direction/T003-reservation-create-reflects-calendar.md
test("T003: 予約作成→カレンダー一覧反映の結合確認", async ({ page, context }) => {
  await loginViaApi(context, "admin001");
  const roomName = uniqueName("T003会議室A");
  const room = await createRoomViaApi(context, roomName, 10);
  await logoutViaApi(context);

  await loginViaUi(page, "user001");

  const date = todayDateString(1); // 翌日(必ず今週内)
  await page.goto(`/reservations/new?room_id=${room.id}&date=${date}`);
  await page.getByLabel("会議室").selectOption(String(room.id));
  await page.getByLabel("日付").fill(date);
  await page.getByLabel("開始時刻").fill("13:00");
  await page.getByLabel("終了時刻").fill("13:30"); // 1コマ(30分)のみ埋めることでセル一致を一意にする
  await page.getByLabel("件名").fill("テスト会議T003");
  await page.getByRole("button", { name: "登録" }).click();

  await page.waitForURL("**/calendar");

  // カレンダーの対象日付タブへ切り替えて確認する。
  await page.getByRole("button", { name: date }).click();
  await expect(page.getByText(`一般花子 / テスト会議T003`)).toBeVisible();
});
