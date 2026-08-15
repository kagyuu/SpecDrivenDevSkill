import { expect, test } from "@playwright/test";
import { createRoomViaApi, loginViaApi, loginViaUi, logoutViaApi, uniqueName } from "./helpers";

// docs/P008-test-direction/T005-my-reservations-period-filter.md
test("T005: マイ予約一覧periodフィルタの結合確認", async ({ page, context }) => {
  await loginViaApi(context, "admin001");
  const room = await createRoomViaApi(context, uniqueName("T005会議室A"), 10);
  await logoutViaApi(context);

  await loginViaApi(context, "user001");
  await context.request.post("/api/reservations", {
    data: { room_id: room.id, date: "2099-01-01", start_time: "10:00", end_time: "11:00", title: "T005未来の予約" },
  });
  await context.request.post("/api/reservations", {
    data: { room_id: room.id, date: "2020-01-01", start_time: "10:00", end_time: "11:00", title: "T005過去の予約" },
  });

  await page.goto("/my-reservations");
  await expect(page.getByText("T005未来の予約")).toBeVisible();
  await expect(page.getByText("T005過去の予約")).not.toBeVisible();

  await page.getByLabel("期間").selectOption("past");
  await expect(page.getByText("T005過去の予約")).toBeVisible();
  await expect(page.getByText("T005未来の予約")).not.toBeVisible();
});
