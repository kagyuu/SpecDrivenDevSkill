// S03 予約作成画面 (docs/P002-frontend-spec.md §3 S03, §6.2)

export function validateReservationInput({ roomId, date, startTime, endTime, title }) {
  if (!roomId) return "会議室を選択してください";
  if (!date) return "日付を入力してください";
  if (!startTime || !endTime) return "開始・終了時刻を入力してください";
  if (endTime <= startTime) return "終了時刻は開始時刻より後である必要があります";
  if (!title || !title.trim()) return "件名を入力してください";
  if (title.length > 100) return "件名は100文字以内で入力してください";
  return null;
}

// 終日チェックボックスON時の開始・終了時刻の既定値(※CR-001により追加)
export function getAllDayDefaults() {
  return { startTime: "09:00", endTime: "18:00" };
}

export function createReservationCreateController(reservationApi) {
  const state = { error: null };
  return {
    getState() {
      return state;
    },
    async submit(input) {
      const validationError = validateReservationInput(input);
      if (validationError) {
        state.error = validationError;
        return { ok: false, message: validationError };
      }
      try {
        const created = await reservationApi.createReservation({
          room_id: input.roomId,
          date: input.date,
          start_time: input.startTime,
          end_time: input.endTime,
          title: input.title,
          participant_ids: input.participantIds || [],
          notes: input.notes || null,
        });
        state.error = null;
        return { ok: true, reservation: created };
      } catch (err) {
        if (err.status === 409) {
          state.error = "選択した会議室・時間帯は既に予約されています";
        } else {
          state.error = err.message;
        }
        return { ok: false, message: state.error };
      }
    },
  };
}

export function mountReservationCreatePage(container, roomApi, userApi, reservationApi, onCreated) {
  const controller = createReservationCreateController(reservationApi);

  async function render() {
    const rooms = await roomApi.list();
    const users = await userApi.list(false);
    const state = controller.getState();
    container.innerHTML = `
      <h2>予約作成</h2>
      <form id="reservation-create-form">
        <div class="form-row"><label>会議室</label>
          <select name="room_id">${rooms.map((r) => `<option value="${r.id}">${r.name}</option>`).join("")}</select>
        </div>
        <div class="form-row"><label>日付</label><input name="date" type="date" /></div>
        <div class="form-row"><label>開始時刻</label><input name="start_time" type="time" /></div>
        <div class="form-row"><label>終了時刻</label><input name="end_time" type="time" /></div>
        <div class="form-row"><label><input name="all_day" type="checkbox" /> 終日</label></div>
        <div class="form-row"><label>件名</label><input name="title" /></div>
        <div class="form-row"><label>参加者</label>
          <select name="participant_ids" multiple>${users.map((u) => `<option value="${u.id}">${u.name}</option>`).join("")}</select>
        </div>
        <div class="form-row"><label>備考</label><textarea name="notes"></textarea></div>
        <button type="submit">登録</button>
        <div class="error-message">${state.error || ""}</div>
      </form>
    `;
    const form = container.querySelector("#reservation-create-form");
    // 終日チェックボックス: ONにした瞬間だけ開始・終了時刻を自動入力する。
    // 自動入力後に利用者が時刻を手動編集した場合は、そのDOM上の値がそのまま
    // submit時に読み取られるため、手動編集を優先する処理は別途不要(※CR-001により追加)。
    form.all_day.addEventListener("change", (e) => {
      if (e.target.checked) {
        const { startTime, endTime } = getAllDayDefaults();
        form.start_time.value = startTime;
        form.end_time.value = endTime;
      }
    });
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const participantIds = Array.from(form.participant_ids.selectedOptions).map((o) => Number(o.value));
      const result = await controller.submit({
        roomId: Number(form.room_id.value), date: form.date.value, startTime: form.start_time.value,
        endTime: form.end_time.value, title: form.title.value, participantIds, notes: form.notes.value,
      });
      if (result.ok && onCreated) onCreated(result.reservation);
      else render();
    });
  }

  render();
  return controller;
}
