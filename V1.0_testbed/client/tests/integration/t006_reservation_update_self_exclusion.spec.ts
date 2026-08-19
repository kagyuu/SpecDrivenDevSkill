import { expect, test } from "@playwright/test";
import { createRoomViaApi, loginViaApi, loginViaUi, logoutViaApi, uniqueName } from "./helpers";

function tomorrowDateString(): string {
  const d = new Date();
  d.setDate(d.getDate() + 1);
  return d.toISOString().slice(0, 10);
}

// docs/P008-test-direction/T006-reservation-update-self-exclusion.md
test("T006: 予約編集(自己除外重複)の結合確認", async ({ page, context }) => {
  await loginViaApi(context, "admin001");
  const room = await createRoomViaApi(context, uniqueName("T006会議室A"), 10);
  await logoutViaApi(context);

  await loginViaApi(context, "user001");
  const date = tomorrowDateString();
  const created = await (
    await context.request.post("/api/reservations", {
      data: { room_id: room.id, date, start_time: "10:00", end_time: "11:00", title: "旧件名T006" },
    })
  ).json();

  await loginViaUi(page, "user001");
  await page.goto(`/reservations/${created.id}`);
  await page.getByLabel("件名").fill("新件名T006");
  await page.getByRole("button", { name: "更新" }).click();

  await page.waitForURL("**/calendar");
  await expect(page.getByRole("alert")).toHaveCount(0);

  const detail = await context.request.get(`/api/reservations/${created.id}`);
  expect((await detail.json()).title).toBe("新件名T006");
});
