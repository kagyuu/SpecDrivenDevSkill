// S06 会議室管理画面(管理者用)。docs/02-frontend-spec.md 1章 S06対応。
import { api } from "../api.js";

export async function renderRoomsAdmin(main, user) {
  if (!user || user.role !== 'admin') {
    main.innerHTML = '<p class="error">この画面は管理者のみ利用できます。</p>';
    return;
  }
  const rooms = await api.listRooms(true);
  let html = '<h2>会議室管理</h2>';
  html += '<table><thead><tr><th>名前</th><th>収容人数</th><th>設備</th><th>有効</th><th></th></tr></thead><tbody>';
  for (const r of rooms) {
    html += `<tr><td>${r.name}</td><td>${r.capacity}</td><td>${r.equipment || ''}</td><td>${r.is_active ? '有効' : '無効'}</td>
      <td>${r.is_active ? `<button data-id="${r.id}" class="del-room">削除</button>` : ''}</td></tr>`;
  }
  html += '</tbody></table>';
  html += `<h3>新規登録</h3>
    <form id="room-form">
      <div><label>名前 <input name="name" required maxlength="50" /></label></div>
      <div><label>収容人数 <input name="capacity" type="number" min="1" required /></label></div>
      <div><label>設備 <input name="equipment" maxlength="200" /></label></div>
      <div class="error" id="room-error"></div>
      <button type="submit">登録</button>
    </form>`;
  main.innerHTML = html;

  document.getElementById('room-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const form = new FormData(e.target);
    try {
      await api.createRoom({
        name: form.get('name'),
        capacity: Number(form.get('capacity')),
        equipment: form.get('equipment'),
      });
      renderRoomsAdmin(main, user);
    } catch (err) {
      document.getElementById('room-error').textContent = err.message;
    }
  });

  main.querySelectorAll('.del-room').forEach((btn) => {
    btn.addEventListener('click', async () => {
      await api.deleteRoom(btn.dataset.id);
      renderRoomsAdmin(main, user);
    });
  });
}
