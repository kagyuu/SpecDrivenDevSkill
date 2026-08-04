import test from "node:test";
import assert from "node:assert/strict";
import { buildCalendarGrid, createCalendarController, generateTimeSlots } from "../js/pages/calendarPage.js";

test("generateTimeSlots covers 9:00-17:30 in 30 minute steps", () => {
  const slots = generateTimeSlots();
  assert.equal(slots[0], "09:00");
  assert.equal(slots[slots.length - 1], "17:30");
  assert.equal(slots.length, 18);
});

test("buildCalendarGrid marks the matching slot as booked", () => {
  const rooms = [{ id: 1, name: "会議室A" }];
  const reservations = [{ room_id: 1, start_time: "10:00", end_time: "11:00", title: "MTG" }];
  const grid = buildCalendarGrid(rooms, reservations);
  const slot1000 = grid[0].slots.find((s) => s.time === "10:00");
  const slot1130 = grid[0].slots.find((s) => s.time === "11:30");
  assert.equal(slot1000.booked, true);
  assert.equal(slot1000.reservation.title, "MTG");
  assert.equal(slot1130.booked, false);
});

test("calendar controller loads rooms and reservations and builds the grid", async () => {
  const fakeRoomApi = { async list() { return [{ id: 1, name: "会議室A" }]; } };
  const fakeReservationApi = {
    async listReservations() {
      return [{ room_id: 1, start_time: "10:00", end_time: "11:00", title: "MTG" }];
    },
  };
  const controller = createCalendarController(fakeRoomApi, fakeReservationApi);
  await controller.load("2026-08-10", "2026-08-10");
  const state = controller.getState();
  assert.equal(state.grid.length, 1);
  assert.equal(state.grid[0].room.name, "会議室A");
});
