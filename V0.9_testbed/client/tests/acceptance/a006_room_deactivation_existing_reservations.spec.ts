import { expect, test } from "@playwright/test";
import { createRoomViaApi, loginViaApi, loginViaUi, logoutViaApi, uniqueName } from "../integration/helpers";

function tomorrowDateString(): string {
  const d = new Date();
  d.setDate(d.getDate() + 1);
  return d.toISOString().slice(0, 10);
}

// docs/P009-acceptance-direction/A006-room-deactivation-existing-reservations.md
test("A006: 会議室無効化後の既存予約の扱い確認", async ({ page, context }) => {
  const roomName = uniqueName("A006会議室D");

  await loginViaApi(context, "admin001");
  const room = await createRoomViaApi(context, roomName, 10);
  await logoutViaApi(context);

  const date = tomorrowDateString();
  await loginViaApi(context, "user001");
  const reservation = await (
    await context.request.post("/api/reservations", {
      data: { room_id: room.id, date, start_time: "10:00", end_time: "11:00", title: "無効化確認用" },
    })
  ).json();
  await logoutViaApi(context);

  // 1. admin001でS06を開き、会議室Dを無効化する。
  await loginViaUi(page, "admin001");
  await page.goto("/rooms");
  page.once("dialog", (dialog) => dialog.accept());
  await page.locator("tr", { hasText: roomName }).getByRole("button", { name: "削除" }).click();
  await expect(page.locator("tr", { hasText: roomName }).getByText("無効")).toBeVisible();
  await logoutViaApi(context);

  // 2. user001で再ログインし、S05・S02で該当予約がまだ表示され、S04から内容確認・取消操作が可能であることを確認する。
  await loginViaUi(page, "user001");
  await page.goto("/my-reservations");
  await expect(page.getByText("無効化確認用")).toBeVisible();

  await page.goto(`/reservations/${reservation.id}`);
  await expect(page.getByLabel("件名")).toHaveValue("無効化確認用");
  await expect(page.getByRole("button", { name: "取消" })).toBeVisible();

  // 3. user001でS03を開き、会議室Dがプルダウンに出ないこと(新規予約はできないこと)を確認する。
  await page.goto("/reservations/new");
  await expect(page.getByLabel("会議室").locator("option", { hasText: roomName })).toHaveCount(0);
});
