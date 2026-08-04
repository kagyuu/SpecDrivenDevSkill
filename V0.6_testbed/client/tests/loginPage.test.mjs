import test from "node:test";
import assert from "node:assert/strict";
import { createLoginController, validateLoginInput } from "../js/pages/loginPage.js";

test("validateLoginInput blocks submission when employee id is empty", () => {
  assert.equal(validateLoginInput("", "Passw0rd1"), "社員IDを入力してください");
});

test("validateLoginInput blocks submission when password is empty", () => {
  assert.equal(validateLoginInput("E0001", ""), "パスワードを入力してください");
});

test("validateLoginInput passes for filled-in fields", () => {
  assert.equal(validateLoginInput("E0001", "Passw0rd1"), null);
});

test("controller calls authApi.login with the given arguments on success", async () => {
  let calledWith = null;
  const fakeAuthApi = {
    async login(employeeId, password) {
      calledWith = [employeeId, password];
      return { id: 1, employee_id: employeeId, name: "山田太郎", role: "general" };
    },
  };
  const controller = createLoginController(fakeAuthApi);
  const result = await controller.submit("E0001", "Passw0rd1");
  assert.deepEqual(calledWith, ["E0001", "Passw0rd1"]);
  assert.equal(result.ok, true);
  assert.equal(result.user.employee_id, "E0001");
});

test("controller surfaces the standard error message on 401", async () => {
  const fakeAuthApi = {
    async login() {
      const err = new Error("bad credentials");
      err.status = 401;
      throw err;
    },
  };
  const controller = createLoginController(fakeAuthApi);
  const result = await controller.submit("E0001", "WrongPassword");
  assert.equal(result.ok, false);
  assert.equal(result.message, "社員IDまたはパスワードが正しくありません");
});

test("controller blocks submission before calling the API when fields are empty", async () => {
  let called = false;
  const fakeAuthApi = {
    async login() {
      called = true;
      return {};
    },
  };
  const controller = createLoginController(fakeAuthApi);
  const result = await controller.submit("", "");
  assert.equal(called, false);
  assert.equal(result.ok, false);
});
