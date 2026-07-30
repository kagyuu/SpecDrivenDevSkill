// S04 予約詳細・編集画面。docs/02-frontend-spec.md 1章 S04対応。
import { api } from "../api.js";

export async function renderReservationDetail(main, id, user) {
  const r = await api.getReservation(id);
  const canEdit = user && (user.id === r.created_by || user.role === 'admin');
  main.innerHTML = `
    <h2>予約詳細</h2>
    <p>会議室: ${r.room_name}</p>
    <p>日付: ${r.date} ${r.start_time}-${r.end_time}</p>
    <p>件名: ${r.subject}</p>
    <p>備考: ${r.notes || ''}</p>
    <p>予約者: ${r.created_by_name}</p>
    ${canEdit ? '<button id="cancel-btn">取消</button>' : '<p>(閲覧のみ: 本人または管理者のみ編集・取消できます)</p>'}
  `;
  if (canEdit) {
    document.getElementById('cancel-btn').addEventListener('click', async () => {
      await api.deleteReservation(id);
      location.hash = '#/calendar';
    });
  }
}
