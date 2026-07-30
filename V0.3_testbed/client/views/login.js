// S01 ログイン画面。docs/02-frontend-spec.md 1章 S01対応。
import { api } from "../api.js";

export function renderLogin(main, onSuccess) {
  main.innerHTML = `
    <h2>ログイン</h2>
    <form id="login-form">
      <div><label>社員ID <input name="employee_id" required maxlength="20" /></label></div>
      <div><label>パスワード <input name="password" type="password" required minlength="8" maxlength="72" /></label></div>
      <div class="error" id="login-error"></div>
      <button type="submit">ログイン</button>
    </form>
  `;
  document.getElementById('login-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const form = new FormData(e.target);
    try {
      const result = await api.login(form.get('employee_id'), form.get('password'));
      onSuccess(result.user);
    } catch (err) {
      document.getElementById('login-error').textContent = 'ユーザーIDまたはパスワードが違います';
    }
  });
}
