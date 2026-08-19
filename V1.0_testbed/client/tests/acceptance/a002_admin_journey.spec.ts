import { expect, test } from "@playwright/test";
import { loginViaApi, loginViaUi, logoutViaApi, uniqueName } from "../integration/helpers";

function todayDateString(): string {
  return new Date().toISOString().slice(0, 10);
}

// docs/P009-acceptance-direction/A002-admin-journey.md
test("A002: 管理者の標準的な業務フロー", async ({ page, context }) => {
  const roomName = uniqueName("A002会議室C");
  const employeeId = uniqueName("a002u").slice(0, 20);

  // 1. admin001でログインしS06で会議室を新規登録
  await loginViaUi(page, "admin001");
  await page.goto("/rooms");
  await page.getByLabel("会議室名").fill(roomName);
  await page.getByLabel("収容人数").fill("6");
  await page.getByRole("button", { name: "登録" }).click();
  await expect(page.getByText(roomName)).toBeVisible();

  // 2. S07で新規ユーザーuser003相当を登録
  await page.goto("/users");
  await page.getByLabel("社員ID").fill(employeeId);
  await page.getByLabel("氏名").fill("新規次郎");
  await page.getByLabel("初期パスワード").fill("NewUser1234");
  await page.getByRole("button", { name: "登録" }).click();
  await expect(page.getByText("新規次郎")).toBeVisible();

  // 3. API経由でuser001の予約を会議室Cに作成する
  await logoutViaApi(context);
  await loginViaApi(context, "admin001");
  const room = (await (await context.request.get("/api/rooms")).json()).find((r: { name: string }) => r.name === roomName);
  await logoutViaApi(context);

  await loginViaApi(context, "user001");
  const date = todayDateString();
  const reservation = await (
    await context.request.post("/api/reservations", {
      data: { room_id: room.id, date, start_time: "09:00", end_time: "10:00", title: "一般ユーザー予約" },
    })
  ).json();
  await logoutViaApi(context);

  // 4. admin001で再ログインし、S02からuser001の予約を開いて件名変更・更新
  await loginViaUi(page, "admin001");
  await page.goto(`/reservations/${reservation.id}`);
  await expect(page.getByLabel("件名")).toBeVisible();
  await page.getByLabel("件名").fill("管理者確認済み");
  await page.getByRole("button", { name: "更新" }).click();
  await page.waitForURL("**/calendar");

  // 5. 同じ予約をS04から取消
  await page.goto(`/reservations/${reservation.id}`);
  page.once("dialog", (dialog) => dialog.accept());
  await page.getByRole("button", { name: "取消" }).click();
  await page.waitForURL("**/calendar");

  const afterDelete = await context.request.get(`/api/reservations/${reservation.id}`, {
    headers: {},
  });
  // admin001としてログイン中のcontextなので404が正しい(削除済み)
  expect(afterDelete.status()).toBe(404);
});
