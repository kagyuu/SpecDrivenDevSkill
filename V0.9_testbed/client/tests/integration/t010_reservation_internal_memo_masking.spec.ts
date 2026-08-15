import { expect, test } from "@playwright/test";
import { createRoomViaApi, loginViaApi, loginViaUi, logoutViaApi, todayDateString, uniqueName } from "./helpers";

// docs/P008-test-direction/T010-reservation-internal-memo-masking.md
// ※CR-001により追加。
test("T010: 予約「備考(社内向けメモ)」の閲覧範囲マスキング結合確認", async ({ page, context }) => {
  await loginViaApi(context, "admin001");
  const roomName = uniqueName("T010会議室A");
  const room = await createRoomViaApi(context, roomName, 10);
  await logoutViaApi(context);

  const date = todayDateString(1);

  // 1. user001でログインし、S03で「備考(社内向けメモ)」に入力して予約を作成する。
  await loginViaUi(page, "user001");
  await page.goto(`/reservations/new?room_id=${room.id}&date=${date}`);
  await page.getByLabel("会議室").selectOption(String(room.id));
  await page.getByLabel("日付").fill(date);
  await page.getByLabel("開始時刻").fill("14:00");
  await page.getByLabel("終了時刻").fill("14:30");
  await page.getByLabel("件名").fill("T010テスト会議");
  await page.getByLabel("備考(社内向けメモ)").fill("非公開メモ");
  await page.getByRole("button", { name: "登録" }).click();
  await page.waitForURL("**/calendar");

  // 作成された予約のIDをAPI経由で特定する(カレンダー一覧はタイトル・予約者のみ表示するため)。
  const listResp = await context.request.get("/api/reservations", {
    params: { date_from: date, date_to: date, room_id: String(room.id) },
  });
  const list = await listResp.json();
  const created = list.find((r: { title: string }) => r.title === "T010テスト会議");
  expect(created).toBeTruthy();
  const reservationId = created.id;

  // 2. 同じuser001でS04を開き、「備考(社内向けメモ)」欄に「非公開メモ」が表示されることを確認する。
  await page.goto(`/reservations/${reservationId}`);
  await expect(page.getByLabel("備考(社内向けメモ)")).toHaveValue("非公開メモ");

  await logoutViaApi(context);

  // 3. admin001でログインし、同じ予約をS04で開き、「非公開メモ」が表示されることを確認する。
  await loginViaUi(page, "admin001");
  await page.goto(`/reservations/${reservationId}`);
  await expect(page.getByLabel("備考(社内向けメモ)")).toHaveValue("非公開メモ");

  await logoutViaApi(context);

  // 4. user002(所有者でも管理者でもない)でログインし、APIレスポンスのinternal_memoがnullであることを確認する。
  await loginViaUi(page, "user002");

  const detailResp = await context.request.get(`/api/reservations/${reservationId}`);
  expect(detailResp.ok()).toBeTruthy();
  const detailBody = await detailResp.json();
  expect(detailBody.internal_memo).toBeNull();

  const calendarResp = await context.request.get("/api/reservations", {
    params: { date_from: date, date_to: date, room_id: String(room.id) },
  });
  const calendarList = await calendarResp.json();
  const sameReservation = calendarList.find((r: { id: number }) => r.id === reservationId);
  expect(sameReservation).toBeTruthy();
  expect(sameReservation.internal_memo).toBeNull();

  // UIで該当予約を開いても内容欄自体が表示されないことも合わせて確認する。
  await page.goto(`/reservations/${reservationId}`);
  await expect(page.getByText(/表示のみ/)).toBeVisible();
  await expect(page.getByLabel("備考(社内向けメモ)")).toHaveCount(0);
});
