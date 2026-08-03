import test from "node:test";
import assert from "node:assert/strict";
import {
  createReservationCreateController,
  getAllDayDefaults,
  validateReservationInput,
} from "../js/pages/reservationCreatePage.js";

const validInput = {
  roomId: 1, date: "2026-08-10", startTime: "10:00", endTime: "11:00", title: "定例MTG",
};

test("validateReservationInput requires a room", () => {
  assert.equal(validateReservationInput({ ...validInput, roomId: null }), "会議室を選択してください");
});

test("validateReservationInput rejects end <= start", () => {
  assert.equal(
    validateReservationInput({ ...validInput, startTime: "11:00", endTime: "10:00" }),
    "終了時刻は開始時刻より後である必要があります",
  );
});

test("validateReservationInput passes for valid input", () => {
  assert.equal(validateReservationInput(validInput), null);
});

test("submit calls reservationApi.createReservation with the right payload", async () => {
  let calledWith = null;
  const fakeApi = {
    async createReservation(data) {
      calledWith = data;
      return { id: 1, ...data };
    },
  };
  const controller = createReservationCreateController(fakeApi);
  const result = await controller.submit(validInput);
  assert.equal(result.ok, true);
  assert.equal(calledWith.room_id, 1);
  assert.equal(calledWith.title, "定例MTG");
});

test("submit surfaces the standard overlap message on 409", async () => {
  const fakeApi = {
    async createReservation() {
      const err = new Error("conflict");
      err.status = 409;
      throw err;
    },
  };
  const controller = createReservationCreateController(fakeApi);
  const result = await controller.submit(validInput);
  assert.equal(result.ok, false);
  assert.equal(result.message, "選択した会議室・時間帯は既に予約されています");
});

// 終日チェックボックス(※CR-001により追加)
test("getAllDayDefaults returns 09:00-18:00", () => {
  assert.deepEqual(getAllDayDefaults(), { startTime: "09:00", endTime: "18:00" });
});

test("all-day defaults satisfy the standard end>start validation", () => {
  const { startTime, endTime } = getAllDayDefaults();
  assert.equal(
    validateReservationInput({ ...validInput, startTime, endTime }),
    null,
  );
});

test("submit accepts the all-day defaults as start/end time payload", async () => {
  let calledWith = null;
  const fakeApi = {
    async createReservation(data) {
      calledWith = data;
      return { id: 2, ...data };
    },
  };
  const controller = createReservationCreateController(fakeApi);
  const { startTime, endTime } = getAllDayDefaults();
  const result = await controller.submit({ ...validInput, startTime, endTime });
  assert.equal(result.ok, true);
  assert.equal(calledWith.start_time, "09:00");
  assert.equal(calledWith.end_time, "18:00");
  assert.equal("all_day" in calledWith, false);
});
