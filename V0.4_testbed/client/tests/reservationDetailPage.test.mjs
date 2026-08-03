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
