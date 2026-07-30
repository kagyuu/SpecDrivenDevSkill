// S02 予約カレンダー画面。docs/02-frontend-spec.md 1章 S02対応。
import { api } from "../api.js";

function startOfWeek(d) {
  const day = d.getDay();
  const diff = d.getDate() - day;
  return new Date(d.setDate(diff));
}

export async function renderCalendar(main, user) {
  main.innerHTML = '<p>読み込み中...</p>';
  const today = new Date();
  const from = startOfWeek(new Date(today));
  const to = new Date(from);
  to.setDate(to.getDate() + 6);
  const dateFrom = from.toISOString().slice(0, 10);
  const dateTo = to.toISOString().slice(0, 10);

  const [rooms, reservations] = await Promise.all([
    api.listRooms(),
    api.listReservations(dateFrom, dateTo),
  ]);

  let html = `<h2>予約カレンダー(${dateFrom} 〜 ${dateTo})</h2>`;
  html += `<p><a href="#/reservation-new">+ 新規予約</a></p>`;
  html += '<table><thead><tr><th>会議室</th><th>予約</th></tr></thead><tbody>';
  for (const room of rooms) {
    const roomReservations = reservations.filter((r) => r.room_id === room.id);
    const cell = roomReservations
      .map((r) => `<a href="#/reservation/${r.id}">${r.date} ${r.start_time}-${r.end_time} ${r.subject}(${r.created_by_name})</a>`)
      .join('<br/>') || '(空き)';
    html += `<tr><td>${room.name}</td><td>${cell}</td></tr>`;
  }
  html += '</tbody></table>';
  main.innerHTML = html;
}
