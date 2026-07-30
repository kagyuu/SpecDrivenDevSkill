// S07 ユーザー管理画面(管理者用)。docs/02-frontend-spec.md 1章 S07対応。
import { api } from "../api.js";

export async function renderUsersAdmin(main, user) {
  if (!user || user.role !== 'admin') {
    main.innerHTML = '<p class="error">この画面は管理者のみ利用できます。</p>';
    return;
  }
  const users = await api.listUsers();
  let html = '<h2>ユーザー管理</h2>';
  html += '<table><thead><tr><th>社員ID</th><th>氏名</th><th>権限</th><th>有効</th><th></th></tr></thead><tbody>';
  for (const u of users) {
    html += `<tr><td>${u.employee_id}</td><td>${u.name}</td><td>${u.role}</td><td>${u.is_active ? '有効' : '無効'}</td>
      <td>${u.is_active ? `<button data-id="${u.id}" class="del-user">削除</button>` : ''}</td></tr>`;
  }
  html += '</tbody></table>';
  html += `<h3>新規登録</h3>
    <form id="user-form">
      <div><label>社員ID <input name="employee_id" required maxlength="20" /></label></div>
      <div><label>氏名 <input name="name" required maxlength="50" /></label></div>
      <div><label>権限
        <select name="role"><option value="general">一般</option><option value="admin">管理者</option></select>
      </label></div>
      <div><label>初期パスワード <input name="password" type="password" required minlength="8" maxlength="72" /></label></div>
      <div class="error" id="user-error"></div>
      <button type="submit">登録</button>
    </form>`;
  main.innerHTML = html;

  document.getElementById('user-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const form = new FormData(e.target);
    try {
      await api.createUser({
        employee_id: form.get('employee_id'),
        name: form.get('name'),
        role: form.get('role'),
        password: form.get('password'),
      });
      renderUsersAdmin(main, user);
    } catch (err) {
      document.getElementById('user-error').textContent = err.message;
    }
  });

  main.querySelectorAll('.del-user').forEach((btn) => {
    btn.addEventListener('click', async () => {
      await api.deleteUser(btn.dataset.id);
      renderUsersAdmin(main, user);
    });
  });
}
