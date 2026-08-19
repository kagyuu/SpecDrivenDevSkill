import { expect, test } from "@playwright/test";
import { createRoomViaApi, loginViaApi, loginViaUi, logoutViaApi, uniqueName } from "./helpers";

function tomorrowDateString(): string {
  const d = new Date();
  d.setDate(d.getDate() + 1);
  return d.toISOString().slice(0, 10);
}

// docs/P008-test-direction/T004-reservation-conflict-display.md
test("T004: 予約重複エラーのフロント表示結合確認", async ({ page, context }) => {
  await loginViaApi(context, "admin001");
  const room = await createRoomViaApi(context, uniqueName("T004会議室A"), 10);
  const date = tomorrowDateString();

  // 既存予約を1件、API経由で用意しておく。
  await context.request.post("/api/reservations", {
    data: { room_id: room.id, date, start_time: "10:00", end_time: "11:00", title: "既存予約" },
  });
  await logoutViaApi(context);

  await loginViaUi(page, "user001");
  await page.goto(`/reservations/new?room_id=${room.id}&date=${date}`);
  await page.getByLabel("会議室").selectOption(String(room.id));
  await page.getByLabel("日付").fill(date);
  await page.getByLabel("開始時刻").fill("10:30");
  await page.getByLabel("終了時刻").fill("11:30");
  await page.getByLabel("件名").fill("重複してみる会議");
  await page.getByRole("button", { name: "登録" }).click();

  await expect(page.getByRole("alert")).toHaveText("選択した会議室・時間帯は既に予約されています");
  // S02へ遷移せずS03に留まること。
  await expect(page).toHaveURL(/\/reservations\/new/);
});
