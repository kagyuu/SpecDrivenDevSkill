import test from "node:test";
import assert from "node:assert/strict";
import { canEdit, createReservationDetailController } from "../js/pages/reservationDetailPage.js";

const baseReservation = {
  id: 10, room_id: 1, date: "2026-08-10", start_time: "10:00", end_time: "11:00",
  title: "定例MTG", created_by: { id: 1, name: "山田太郎" }, participants: [],
};

test("canEdit is true for the owner", () => {
  assert.equal(canEdit(baseReservation, { id: 1, role: "general" }), true);
});

test("canEdit is true for admins", () => {
  assert.equal(canEdit(baseReservation, { id: 999, role: "admin" }), true);
});

test("canEdit is false for other general users (read-only)", () => {
  assert.equal(canEdit(baseReservation, { id: 2, role: "general" }), false);
});

test("submitUpdate calls reservationApi.update and stores the result", async () => {
  let calledWith = null;
  const fakeApi = {
    async update(id, data) {
      calledWith = [id, data];
      return { ...baseReservation, title: data.title };
    },
  };
  const controller = createReservationDetailController(fakeApi);
  const result = await controller.submitUpdate(10, {
    roomId: 1, date: "2026-08-10", startTime: "10:00", endTime: "11:00", title: "定例MTG(変更後)",
  });
  assert.equal(result.ok, true);
  assert.equal(calledWith[0], 10);
  assert.equal(result.reservation.title, "定例MTG(変更後)");
});

test("submitUpdate surfaces 409 error and does not navigate away", async () => {
  const fakeApi = {
    async update() {
      const err = new Error("conflict");
      err.status = 409;
      throw err;
    },
  };
  const controller = createReservationDetailController(fakeApi);
  const result = await controller.submitUpdate(10, {
    roomId: 1, date: "2026-08-10", startTime: "13:00", endTime: "14:00", title: "定例MTG",
  });
  assert.equal(result.ok, false);
  assert.equal(result.message, "選択した会議室・時間帯は既に予約されています");
});

test("submitDelete calls reservationApi.remove", async () => {
  let removed = null;
  const fakeApi = { async remove(id) { removed = id; } };
  const controller = createReservationDetailController(fakeApi);
  const result = await controller.submitDelete(10);
  assert.equal(result.ok, true);
  assert.equal(removed, 10);
});

// 参加予定人数(※CR-003により追加)
test("submitUpdate sends attendee_count in the payload", async () => {
  let calledWith = null;
  const fakeApi = {
    async update(id, data) {
      calledWith = [id, data];
      return { ...baseReservation, attendee_count: data.attendee_count };
    },
  };
  const controller = createReservationDetailController(fakeApi);
  const result = await controller.submitUpdate(10, {
    roomId: 1, date: "2026-08-10", startTime: "10:00", endTime: "11:00", title: "定例MTG",
    attendeeCount: "9",
  });
  assert.equal(result.ok, true);
  assert.equal(calledWith[1].attendee_count, 9);
  assert.equal(result.reservation.attendee_count, 9);
});

test("submitUpdate sends attendee_count as null when cleared", async () => {
  let calledWith = null;
  const fakeApi = {
    async update(id, data) {
      calledWith = [id, data];
      return { ...baseReservation, attendee_count: data.attendee_count };
    },
  };
  const controller = createReservationDetailController(fakeApi);
  await controller.submitUpdate(10, {
    roomId: 1, date: "2026-08-10", startTime: "10:00", endTime: "11:00", title: "定例MTG",
    attendeeCount: "",
  });
  assert.equal(calledWith[1].attendee_count, null);
});

test("submitUpdate rejects an invalid attendee count before calling the API", async () => {
  let called = false;
  const fakeApi = { async update() { called = true; return baseReservation; } };
  const controller = createReservationDetailController(fakeApi);
  const result = await controller.submitUpdate(10, {
    roomId: 1, date: "2026-08-10", startTime: "10:00", endTime: "11:00", title: "定例MTG",
    attendeeCount: 0,
  });
  assert.equal(result.ok, false);
  assert.equal(result.message, "参加予定人数は1以上の整数で入力してください");
  assert.equal(called, false);
});

test("submitUpdate surfaces the capacity message on a 400 with field=attendee_count", async () => {
  const fakeApi = {
    async update() {
      const err = new Error("参加予定人数が会議室の収容人数(10名)を超えています");
      err.status = 400;
      err.details = [{ field: "attendee_count", reason: "exceeds room capacity" }];
      throw err;
    },
  };
  const controller = createReservationDetailController(fakeApi);
  const result = await controller.submitUpdate(10, {
    roomId: 1, date: "2026-08-10", startTime: "10:00", endTime: "11:00", title: "定例MTG",
    attendeeCount: 11,
  });
  assert.equal(result.ok, false);
  assert.equal(result.message, "参加予定人数が会議室の収容人数を超えています");
});
