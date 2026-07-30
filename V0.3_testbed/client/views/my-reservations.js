// S05 マイ予約一覧画面。docs/02-frontend-spec.md 1章 S05対応。
import { api } from "../api.js";

export async function renderMyReservations(main) {
  main.innerHTML = '<p>読み込み中...</p>';
  const period = 'future';
  const reservations = await api.listMyReservations(period);
  let html = '<h2>マイ予約一覧</h2>';
  html += '<table><thead><tr><th>日付</th><th>会議室</th><th>時間帯</th><th>件名</th></tr></thead><tbody>';
  for (const r of reservations) {
    html += `<tr><td><a href="#/reservation/${r.id}">${r.date}</a></td><td>${r.room_name}</td><td>${r.start_time}-${r.end_time}</td><td>${r.subject}</td></tr>`;
  }
  html += '</tbody></table>';
  main.innerHTML = html;
}
