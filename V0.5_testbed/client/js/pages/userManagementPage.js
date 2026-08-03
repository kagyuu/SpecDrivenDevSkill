// S07 ユーザー管理画面 (docs/P002-frontend-spec.md §3 S07, §4.14〜§4.17)

export function validateUserInput(employeeId, name, role, initialPassword) {
  if (!employeeId || !/^[A-Za-z0-9]{1,20}$/.test(employeeId)) {
    return "社員IDは半角英数字1〜20文字で入力してください";
  }
  if (!name || !name.trim() || name.length > 50) {
    return "氏名は1〜50文字で入力してください";
  }
  if (role !== "general" && role !== "admin") {
    return "権限を選択してください";
  }
  const hasAlpha = /[A-Za-z]/.test(initialPassword || "");
  const hasDigit = /[0-9]/.test(initialPassword || "");
  if (!initialPassword || initialPassword.length < 8 || !hasAlpha || !hasDigit) {
    return "初期パスワードは8文字以上、英字・数字を含めてください";
  }
  return null;
}

/**
 * ユーザー管理画面のコントローラ。DOMに依存しない。
 * @param {{list: Function, create: Function, update: Function, remove: Function}} userApi
 */
export function createUserManagementController(userApi) {
  const state = { users: [], error: null };

  return {
    getState() {
      return state;
    },
    async loadUsers() {
      state.users = await userApi.list(true);
      return state.users;
    },
    async submitCreate(employeeId, name, role, initialPassword, isActive = true) {
      const validationError = validateUserInput(employeeId, name, role, initialPassword);
      if (validationError) {
        state.error = validationError;
        return { ok: false, message: validationError };
      }
      try {
        await userApi.create({
          employee_id: employeeId, name, role, is_active: isActive, initial_password: initialPassword,
        });
        state.error = null;
        await this.loadUsers();
        return { ok: true };
      } catch (err) {
        state.error = err.message;
        return { ok: false, message: err.message };
      }
    },
    async submitDeactivate(userId) {
      try {
        await userApi.remove(userId);
        state.error = null;
        await this.loadUsers();
        return { ok: true };
      } catch (err) {
        state.error = err.message;
        return { ok: false, message: err.message };
      }
    },
  };
}

export function mountUserManagementPage(container, userApi) {
  const controller = createUserManagementController(userApi);

  async function render() {
    const state = controller.getState();
    container.innerHTML = `
      <h2>ユーザー管理</h2>
      <table>
        <thead><tr><th>社員ID</th><th>氏名</th><th>権限</th><th>状態</th><th></th></tr></thead>
        <tbody>
          ${state.users.map((u) => `
            <tr>
              <td>${u.employee_id}</td><td>${u.name}</td><td>${u.role}</td>
              <td>${u.is_active ? "有効" : "無効"}</td>
              <td><button data-deactivate="${u.id}" ${u.is_active ? "" : "disabled"}>無効化</button></td>
            </tr>`).join("")}
        </tbody>
      </table>
      <form id="user-create-form">
        <div class="form-row"><label>社員ID</label><input name="employee_id" /></div>
        <div class="form-row"><label>氏名</label><input name="name" /></div>
        <div class="form-row"><label>権限</label>
          <select name="role"><option value="general">一般</option><option value="admin">管理者</option></select>
        </div>
        <div class="form-row"><label>初期パスワード</label><input name="initial_password" type="password" /></div>
        <button type="submit">登録</button>
        <div class="error-message">${state.error || ""}</div>
      </form>
    `;
    container.querySelector("#user-create-form").addEventListener("submit", async (e) => {
      e.preventDefault();
      const form = e.target;
      await controller.submitCreate(
        form.employee_id.value, form.name.value, form.role.value, form.initial_password.value,
      );
      render();
    });
    container.querySelectorAll("[data-deactivate]").forEach((btn) => {
      btn.addEventListener("click", async () => {
        await controller.submitDeactivate(Number(btn.dataset.deactivate));
        render();
      });
    });
  }

  controller.loadUsers().then(render);
  return controller;
}
