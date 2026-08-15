import { expect, test } from "@playwright/test";
import { createRoomViaApi, loginViaApi, logoutViaApi, uniqueName } from "../integration/helpers";

function todayDateString(): string {
  return new Date().toISOString().slice(0, 10);
}

// docs/P009-acceptance-direction/A004-reservation-conflict-system-check.md
test("A004: 予約重複防止のシステム全体確認(境界値を含む)", async ({ context }) => {
  await loginViaApi(context, "admin001");
  const room = await createRoomViaApi(context, uniqueName("A004会議室A"), 10);
  await logoutViaApi(context);

  const date = todayDateString();

  // 1. user001で会議室Aに10:00-11:00の予約を作成する。
  await loginViaApi(context, "user001");
  const first = await context.request.post("/api/reservations", {
    data: { room_id: room.id, date, start_time: "10:00", end_time: "11:00", title: "A004手順1" },
  });
  expect(first.status()).toBe(201);
  await logoutViaApi(context);

  // 2. user002で同じ会議室Aに10:30-11:30の予約を作成しようとする(重なる時間帯)。
  await loginViaApi(context, "user002");
  const overlapping = await context.request.post("/api/reservations", {
    data: { room_id: room.id, date, start_time: "10:30", end_time: "11:30", title: "A004手順2" },
  });
  expect(overlapping.status()).toBe(409);
  expect((await overlapping.json()).error_code).toBe("RESERVATION_CONFLICT");

  // 3. user002で同じ会議室Aに11:00-12:00の予約を作成しようとする(手順1の終了時刻から始まる、背中合わせの時間帯)。
  // docs/P003-backend-spec.md §5.9: 背中合わせの予約は重複とみなさないため201になる。
  // ※P202 F004にもとづき訂正(訂正前は誤って409を期待していた。根拠は docs/P202-fix-plan/fixed/F004-*.md 参照)。
  const backToBackAfter = await context.request.post("/api/reservations", {
    data: { room_id: room.id, date, start_time: "11:00", end_time: "12:00", title: "A004手順3" },
  });
  expect(backToBackAfter.status()).toBe(201);

  // 4. user002で同じ会議室Aに09:00-10:00の予約を作成しようとする(手順1の開始時刻に終わる、背中合わせの時間帯)。
  // 同じ理由で201になる。※P202 F004にもとづき訂正。
  const backToBackBefore = await context.request.post("/api/reservations", {
    data: { room_id: room.id, date, start_time: "09:00", end_time: "10:00", title: "A004手順4" },
  });
  expect(backToBackBefore.status()).toBe(201);
});
