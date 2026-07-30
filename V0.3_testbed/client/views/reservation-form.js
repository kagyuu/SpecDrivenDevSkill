// S03 予約作成画面。docs/02-frontend-spec.md 1章 S03対応。
import { api } from "../api.js";

export async function renderReservationForm(main, existing) {
  const rooms = await api.listRooms();
  const roomOptions = rooms.map((r) => `<option value="${r.id}">${r.name}</option>`).join('');
  main.innerHTML = `
    <h2>予約作成</h2>
    <form id="reservation-form">
      <div><label>会議室 <select name="room_id" required>${roomOptions}</select></label></div>
      <div><label>日付 <input name="date" type="date" required /></label></div>
      <div><label>開始時刻 <input name="start_time" type="time" required /></label></div>
      <div><label>終了時刻 <input name="end_time" type="time" required /></label></div>
      <div><label>件名 <input name="subject" required maxlength="100" /></label></div>
      <div><label>備考 <textarea name="notes" maxlength="500"></textarea></label></div>
      <div class="error" id="reservation-error"></div>
      <button type="submit">登録</button>
    </form>
  `;
  document.getElementById('reservation-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const form = new FormData(e.target);
    try {
      await api.createReservation({
        room_id: Number(form.get('room_id')),
        date: form.get('date'),
        start_time: form.get('start_time'),
        end_time: form.get('end_time'),
        subject: form.get('subject'),
        notes: form.get('notes'),
        participant_ids: [],
      });
      location.hash = '#/calendar';
    } catch (err) {
      document.getElementById('reservation-error').textContent =
        err.status === 409 ? '指定の時間帯は既に予約されています' : err.message;
    }
  });
}
