import test from "node:test";
import assert from "node:assert/strict";
import { createMyReservationsController } from "../js/pages/myReservationsPage.js";

test("load defaults to upcoming period", async () => {
  let calledWith = null;
  const fakeApi = {
    async getMine(period) {
      calledWith = period;
      return [{ id: 1, title: "定例MTG" }];
    },
  };
  const controller = createMyReservationsController(fakeApi);
  await controller.load();
  assert.equal(calledWith, "upcoming");
  assert.equal(controller.getState().reservations.length, 1);
});

test("load respects the past period filter", async () => {
  const fakeApi = {
    async getMine(period) {
      return period === "past" ? [{ id: 2, title: "過去MTG" }] : [];
    },
  };
  const controller = createMyReservationsController(fakeApi);
  await controller.load("past");
  assert.equal(controller.getState().reservations[0].title, "過去MTG");
});
