import test from "node:test";
import assert from "node:assert/strict";
import {
  createReservationCreateController,
  getAllDayDefaults,
  normalizeAttendeeCount,
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

// 参加予定人数(※CR-003により追加)
test("validateReservationInput allows a missing attendee count", () => {
  assert.equal(validateReservationInput({ ...validInput, attendeeCount: null }), null);
  assert.equal(validateReservationInput({ ...validInput, attendeeCount: "" }), null);
  assert.equal(validateReservationInput({ ...validInput }), null);
});

test("validateReservationInput accepts a positive integer attendee count", () => {
  assert.equal(validateReservationInput({ ...validInput, attendeeCount: 8 }), null);
  assert.equal(validateReservationInput({ ...validInput, attendeeCount: "8" }), null);
});

test("validateReservationInput rejects a non-positive or non-integer attendee count", () => {
  const message = "参加予定人数は1以上の整数で入力してください";
  assert.equal(validateReservationInput({ ...validInput, attendeeCount: 0 }), message);
  assert.equal(validateReservationInput({ ...validInput, attendeeCount: -1 }), message);
  assert.equal(validateReservationInput({ ...validInput, attendeeCount: 1.5 }), message);
});

test("normalizeAttendeeCount converts empty input to null and numeric input to a number", () => {
  assert.equal(normalizeAttendeeCount(""), null);
  assert.equal(normalizeAttendeeCount(null), null);
  assert.equal(normalizeAttendeeCount(undefined), null);
  assert.equal(normalizeAttendeeCount("8"), 8);
  assert.equal(normalizeAttendeeCount(8), 8);
});

test("submit sends attendee_count in the payload", async () => {
  let calledWith = null;
  const fakeApi = {
    async createReservation(data) {
      calledWith = data;
      return { id: 3, ...data };
    },
  };
  const controller = createReservationCreateController(fakeApi);
  const result = await controller.submit({ ...validInput, attendeeCount: "8" });
  assert.equal(result.ok, true);
  assert.equal(calledWith.attendee_count, 8);
});

test("submit sends attendee_count as null when it is not entered", async () => {
  let calledWith = null;
  const fakeApi = {
    async createReservation(data) {
      calledWith = data;
      return { id: 4, ...data };
    },
  };
  const controller = createReservationCreateController(fakeApi);
  await controller.submit({ ...validInput, attendeeCount: "" });
  assert.equal(calledWith.attendee_count, null);
});

test("submit surfaces the capacity message on a 400 with field=attendee_count", async () => {
  const fakeApi = {
    async createReservation() {
      const err = new Error("参加予定人数が会議室の収容人数(10名)を超えています");
      err.status = 400;
      err.code = "VALIDATION_ERROR";
      err.details = [{ field: "attendee_count", reason: "exceeds room capacity" }];
      throw err;
    },
  };
  const controller = createReservationCreateController(fakeApi);
  const result = await controller.submit({ ...validInput, attendeeCount: 11 });
  assert.equal(result.ok, false);
  assert.equal(result.message, "参加予定人数が会議室の収容人数を超えています");
});

test("submit keeps the raw message for other 400 errors", async () => {
  const fakeApi = {
    async createReservation() {
      const err = new Error("件名は1〜100文字で入力してください");
      err.status = 400;
      err.details = [{ field: "title", reason: "invalid length" }];
      throw err;
    },
  };
  const controller = createReservationCreateController(fakeApi);
  const result = await controller.submit(validInput);
  assert.equal(result.message, "件名は1〜100文字で入力してください");
});
