import test from "node:test";
import assert from "node:assert/strict";
import { createUserManagementController, validateUserInput } from "../js/pages/userManagementPage.js";

test("validateUserInput requires valid employee id", () => {
  assert.equal(
    validateUserInput("###", "鈴木花子", "general", "Passw0rd1"),
    "社員IDは半角英数字1〜20文字で入力してください",
  );
});

test("validateUserInput requires a valid role", () => {
  assert.equal(
    validateUserInput("E0002", "鈴木花子", "manager", "Passw0rd1"),
    "権限を選択してください",
  );
});

test("validateUserInput requires initial password policy", () => {
  assert.equal(
    validateUserInput("E0002", "鈴木花子", "general", "weak"),
    "初期パスワードは8文字以上、英字・数字を含めてください",
  );
});

test("validateUserInput passes for valid input", () => {
  assert.equal(validateUserInput("E0002", "鈴木花子", "general", "Passw0rd1"), null);
});

test("submitCreate calls userApi.create with expected payload", async () => {
  let calledWith = null;
  const fakeApi = {
    async list() { return []; },
    async create(data) { calledWith = data; return { id: 2, ...data }; },
  };
  const controller = createUserManagementController(fakeApi);
  const result = await controller.submitCreate("E0002", "鈴木花子", "general", "Passw0rd1");
  assert.equal(result.ok, true);
  assert.equal(calledWith.employee_id, "E0002");
  assert.equal(calledWith.initial_password, "Passw0rd1");
});

test("submitCreate surfaces duplicate employee id error and does not refresh list", async () => {
  let listCallCount = 0;
  const fakeApi = {
    async list() { listCallCount += 1; return []; },
    async create() {
      const err = new Error("社員IDが既に使用されています");
      err.status = 400;
      throw err;
    },
  };
  const controller = createUserManagementController(fakeApi);
  const result = await controller.submitCreate("E0002", "鈴木花子", "general", "Passw0rd1");
  assert.equal(result.ok, false);
  assert.equal(result.message, "社員IDが既に使用されています");
  assert.equal(listCallCount, 0);
});
