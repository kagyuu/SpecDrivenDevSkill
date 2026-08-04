// S01 ログイン画面 (docs/P002-frontend-spec.md §3 S01, §4.1, §6.1)
//
// ★deviation★ このファイルは「テスト可能なコントローラ関数」(DOM非依存、node --testで
// 単体テスト対象)と「実際のDOM描画」(mountLoginPage、手動/結合確認のみ)を分離している。
// jsdom等のDOM実装がnpmレジストリ制約でインストールできないため(docs/P101-impl-context.md)。

/**
 * ログインフォームの入力チェック。未入力があれば送信をブロックする。
 * @returns {string|null} エラーメッセージ、問題なければnull
 */
export function validateLoginInput(employeeId, password) {
  if (!employeeId || !employeeId.trim()) {
    return "社員IDを入力してください";
  }
  if (!password) {
    return "パスワードを入力してください";
  }
  return null;
}

/**
 * ログイン送信のコントローラ。DOMに依存しないためunit test対象にできる。
 * @param {{login: Function}} authApi
 */
export function createLoginController(authApi) {
  return {
    async submit(employeeId, password) {
      const validationError = validateLoginInput(employeeId, password);
      if (validationError) {
        return { ok: false, message: validationError };
      }
      try {
        const user = await authApi.login(employeeId, password);
        return { ok: true, user };
      } catch (err) {
        if (err.status === 401) {
          return { ok: false, message: "社員IDまたはパスワードが正しくありません" };
        }
        return { ok: false, message: err.message || "ログインに失敗しました" };
      }
    },
  };
}

/**
 * 実際のDOMにログイン画面を描画する(手動/結合確認用。U001-6で疎通確認する)。
 */
export function mountLoginPage(container, authApi, onSuccess) {
  const controller = createLoginController(authApi);
  container.innerHTML = `
    <form id="login-form">
      <div class="form-row">
        <label for="employee_id">社員ID</label>
        <input id="employee_id" name="employee_id" type="text" autocomplete="username" />
      </div>
      <div class="form-row">
        <label for="password">パスワード</label>
        <input id="password" name="password" type="password" autocomplete="current-password" />
      </div>
      <button type="submit">ログイン</button>
      <div class="error-message" id="login-error"></div>
    </form>
  `;
  const form = container.querySelector("#login-form");
  const errorBox = container.querySelector("#login-error");
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    errorBox.textContent = "";
    const employeeId = container.querySelector("#employee_id").value;
    const password = container.querySelector("#password").value;
    const result = await controller.submit(employeeId, password);
    if (!result.ok) {
      errorBox.textContent = result.message;
      return;
    }
    // eslint-disable-next-line no-console
    console.log("login success", result.user);
    if (onSuccess) onSuccess(result.user);
  });
}
