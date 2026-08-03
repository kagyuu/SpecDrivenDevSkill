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
  assert.deepEqual(createCalledWith, {
    name: "会議室A", capacity: 6, equipment: [], is_active: true, description: null,
  });
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

// --- CR-002: 会議室説明文(description)。docs/P007-impl-direction/U006-cr-002-room-description.md U006-2参照 ---

test("validateRoomInput allows a description up to 200 characters", () => {
  assert.equal(validateRoomInput("会議室A", 6, "A".repeat(200)), null);
});

test("validateRoomInput rejects a description over 200 characters", () => {
  assert.equal(
    validateRoomInput("会議室A", 6, "A".repeat(201)),
    "説明文は200文字以内で入力してください",
  );
});

test("submitCreate sends description to roomApi.create", async () => {
  let createCalledWith = null;
  const fakeApi = {
    async list() { return [{ id: 1, name: "会議室A", capacity: 6, is_active: true, description: "個室です" }]; },
    async create(data) { createCalledWith = data; return { id: 1, ...data }; },
  };
  const controller = createRoomManagementController(fakeApi);
  const result = await controller.submitCreate("会議室A", 6, [], true, "個室です");
  assert.equal(result.ok, true);
  assert.equal(createCalledWith.description, "個室です");
});

test("startEdit sets editingRoomId in state", async () => {
  const fakeApi = { async list() { return [{ id: 5, name: "会議室A", capacity: 6, is_active: true }]; } };
  const controller = createRoomManagementController(fakeApi);
  await controller.loadRooms();
  controller.startEdit(5);
  assert.equal(controller.getState().editingRoomId, 5);
});

test("cancelEdit clears editingRoomId", () => {
  const controller = createRoomManagementController({ async list() { return []; } });
  controller.startEdit(5);
  controller.cancelEdit();
  assert.equal(controller.getState().editingRoomId, null);
});

test("submitUpdate calls roomApi.update with description and refreshes the list, clearing editingRoomId", async () => {
  let updateCalledWith = null;
  let listCallCount = 0;
  const fakeApi = {
    async list() {
      listCallCount += 1;
      return listCallCount === 1
        ? [{ id: 5, name: "会議室A", capacity: 6, is_active: true, description: "旧説明" }]
        : [{ id: 5, name: "会議室A", capacity: 10, is_active: true, description: "新説明" }];
    },
    async update(roomId, data) { updateCalledWith = { roomId, data }; return { id: roomId, ...data }; },
  };
  const controller = createRoomManagementController(fakeApi);
  await controller.loadRooms();
  controller.startEdit(5);
  const result = await controller.submitUpdate(5, "会議室A", 10, [], true, "新説明");
  assert.equal(result.ok, true);
  assert.equal(updateCalledWith.roomId, 5);
  assert.equal(updateCalledWith.data.description, "新説明");
  assert.equal(updateCalledWith.data.capacity, 10);
  assert.equal(controller.getState().editingRoomId, null);
  assert.equal(controller.getState().rooms[0].description, "新説明");
});

test("submitUpdate surfaces API error without refreshing the list or clearing editingRoomId", async () => {
  let listCallCount = 0;
  const fakeApi = {
    async list() {
      listCallCount += 1;
      return [{ id: 5, name: "会議室A", capacity: 6, is_active: true, description: "旧説明" }];
    },
    async update() {
      const err = new Error("説明文は200文字以内で入力してください");
      err.status = 400;
      throw err;
    },
  };
  const controller = createRoomManagementController(fakeApi);
  await controller.loadRooms();
  controller.startEdit(5);
  const callCountAfterLoad = listCallCount;
  const result = await controller.submitUpdate(5, "会議室A", 6, [], true, "A".repeat(201));
  assert.equal(result.ok, false);
  assert.equal(listCallCount, callCountAfterLoad); // list not refreshed on error
  assert.equal(controller.getState().editingRoomId, 5); // stays in edit mode on error
});
