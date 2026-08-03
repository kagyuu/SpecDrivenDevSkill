import test from "node:test";
import assert from "node:assert/strict";
import { createRoomManagementController, validateRoomInput } from "../js/pages/roomManagementPage.js";

test("validateRoomInput requires a name", () => {
  assert.equal(validateRoomInput("", 6), "会議室名を入力してください");
});

test("validateRoomInput requires capacity >= 1", () => {
  assert.equal(validateRoomInput("会議室A", 0), "収容人数は1以上の整数で入力してください");
});

test("validateRoomInput passes for valid input", () => {
  assert.equal(validateRoomInput("会議室A", 6), null);
});

test("loadRooms populates state from mock data", async () => {
  const fakeApi = {
    async list() {
      return [{ id: 1, name: "会議室A", capacity: 6, is_active: true }];
    },
  };
  const controller = createRoomManagementController(fakeApi);
  await controller.loadRooms();
  assert.equal(controller.getState().rooms.length, 1);
  assert.equal(controller.getState().rooms[0].name, "会議室A");
});

test("submitCreate calls roomApi.create and refreshes the list", async () => {
  let createCalledWith = null;
  let listCallCount = 0;
  const fakeApi = {
    async list() {
      listCallCount += 1;
      return listCallCount === 1 ? [] : [{ id: 1, name: "会議室A", capacity: 6, is_active: true }];
    },
    async create(data) {
      createCalledWith = data;
      return { id: 1, ...data };
    },
  };
  const controller = createRoomManagementController(fakeApi);
  await controller.loadRooms();
  const result = await controller.submitCreate("会議室A", 6);
  assert.equal(result.ok, true);
  assert.deepEqual(createCalledWith, { name: "会議室A", capacity: 6, equipment: [], is_active: true });
  assert.equal(controller.getState().rooms.length, 1);
});

test("submitCreate does not call the API when validation fails", async () => {
  let called = false;
  const fakeApi = {
    async list() { return []; },
    async create() { called = true; return {}; },
  };
  const controller = createRoomManagementController(fakeApi);
  const result = await controller.submitCreate("", 6);
  assert.equal(called, false);
  assert.equal(result.ok, false);
});

test("submitCreate surfaces API error without refreshing the list", async () => {
  let listCallCount = 0;
  const fakeApi = {
    async list() {
      listCallCount += 1;
      return [];
    },
    async create() {
      const err = new Error("同名の会議室が既に登録されています");
      err.status = 400;
      throw err;
    },
  };
  const controller = createRoomManagementController(fakeApi);
  await controller.loadRooms();
  const callCountAfterLoad = listCallCount;
  const result = await controller.submitCreate("会議室A", 6);
  assert.equal(result.ok, false);
  assert.equal(result.message, "同名の会議室が既に登録されています");
  assert.equal(listCallCount, callCountAfterLoad); // list not refreshed on error
});
