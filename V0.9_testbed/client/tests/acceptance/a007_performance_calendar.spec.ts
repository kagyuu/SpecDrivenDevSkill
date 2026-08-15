import { expect, test } from "@playwright/test";
import { createRoomViaApi, loginViaApi, loginViaUi, logoutViaApi, uniqueName } from "../integration/helpers";

function todayDateString(offsetDays = 0): string {
  const d = new Date();
  d.setDate(d.getDate() + offsetDays);
  return d.toISOString().slice(0, 10);
}

// docs/P009-acceptance-direction/A007-performance-calendar.md
// 開発環境上の参考値であり、本番相当環境でのSLA保証ではない(docs/P009-acceptance-direction/A007-*.md 本文の注記どおり)。
test("A007: カレンダー表示の応答性確認(開発環境上の参考値)", async ({ page, context }) => {
  test.setTimeout(120_000);

  await loginViaApi(context, "admin001");
  const rooms = [];
  for (let i = 0; i < 10; i += 1) {
    rooms.push(await createRoomViaApi(context, uniqueName(`A007会議室${i}`), 10));
  }

  // 1週間 x 全会議室 x 1日3件 = 約210件
  for (let day = 0; day < 7; day += 1) {
    const date = todayDateString(day);
    for (const room of rooms) {
      const slots = [
        ["09:00", "10:00"],
        ["11:00", "12:00"],
        ["14:00", "15:00"],
      ];
      for (const [start, end] of slots) {
        await context.request.post("/api/reservations", {
          data: { room_id: room.id, date, start_time: start, end_time: end, title: `A007-${room.id}-${date}-${start}` },
        });
      }
    }
  }
  await logoutViaApi(context);

  const measurements: number[] = [];
  for (let i = 0; i < 3; i += 1) {
    await loginViaUi(page, "user001");
    const start = Date.now();
    await page.waitForSelector("table"); // RoomTimeGridの描画完了を待つ
    await expect(page.locator("table tbody tr").first()).toBeVisible();
    const elapsed = Date.now() - start;
    measurements.push(elapsed);

    await page.context().request.post("/api/auth/logout");
    await page.context().clearCookies();
  }

  for (const [i, ms] of measurements.entries()) {
    expect(ms, `${i + 1}回目の計測: ${ms}ms`).toBeLessThan(3000);
  }
});
