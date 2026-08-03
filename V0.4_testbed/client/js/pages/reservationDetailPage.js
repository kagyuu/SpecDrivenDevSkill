// S04 予約詳細・編集画面 (docs/P002-frontend-spec.md §3 S04)

import { validateReservationInput } from "./reservationCreatePage.js";

/** 予約者本人または管理者のみ編集可能 (docs/P003-backend-spec.md §4)。 */
export function canEdit(reservation, currentUser) {
  return reservation.created_by.id === currentUser.id || currentUser.role === "admin";
}

export function createReservationDetailController(reservationApi) {
  const state = { reservation: null, error: null };
  return {
    getState() {
      return state;
    },
    async load(reservationId) {
      state.reservation = await reservationApi.getDetail(reservationId);
      return state.reservation;
    },
    async submitUpdate(reservationId, input) {
      const validationError = validateReservationInput(input);
      if (validationError) {
        state.error = validationError;
        return { ok: false, message: validationError };
      }
      try {
        const updated = await reservationApi.update(reservationId, {
          room_id: input.roomId, date: input.date, start_time: input.startTime,
          end_time: input.endTime, title: input.title,
          participant_ids: input.participantIds || [], notes: input.notes || null,
        });
        state.reservation = updated;
        state.error = null;
        return { ok: true, reservation: updated };
      } catch (err) {
        state.error = err.status === 409
          ? "選択した会議室・時間帯は既に予約されています"
          : err.message;
        return { ok: false, message: state.error };
      }
    },
    async submitDelete(reservationId) {
      try {
        await reservationApi.remove(reservationId);
        return { ok: true };
      } catch (err) {
        state.error = err.message;
        return { ok: false, message: err.message };
      }
    },
  };
}

export function mountReservationDetailPage(container, reservationApi, currentUser, reservationId, onDeleted) {
  const controller = createReservationDetailController(reservationApi);

  async function render() {
    await controller.load(reservationId);
    const state = controller.getState();
    const reservation = state.reservation;
    const editable = canEdit(reservation, currentUser);
    container.innerHTML = `
      <h2>予約詳細</h2>
      <form id="detail-form">
        <div class="form-row"><label>件名</label>
          <input name="title" value="${reservation.title}" ${editable ? "" : "readonly"} />
        </div>
        <div class="form-row"><label>日付</label>
          <input name="date" type="date" value="${reservation.date}" ${editable ? "" : "readonly"} />
        </div>
        <div class="form-row"><label>開始</label>
          <input name="start_time" type="time" value="${reservation.start_time}" ${editable ? "" : "readonly"} />
        </div>
        <div class="form-row"><label>終了</label>
          <input name="end_time" type="time" value="${reservation.end_time}" ${editable ? "" : "readonly"} />
        </div>
        <p>予約者: ${reservation.created_by.name}</p>
        ${editable ? '<button type="submit">更新</button><button type="button" id="cancel-btn">取消</button>' : ""}
        <div class="error-message">${state.error || ""}</div>
      </form>
    `;
    if (editable) {
      container.querySelector("#detail-form").addEventListener("submit", async (e) => {
        e.preventDefault();
        const form = e.target;
        await controller.submitUpdate(reservationId, {
          roomId: reservation.room_id, date: form.date.value, startTime: form.start_time.value,
          endTime: form.end_time.value, title: form.title.value,
        });
        render();
      });
      container.querySelector("#cancel-btn").addEventListener("click", async () => {
        if (!window.confirm || window.confirm("この予約を取消しますか?")) {
          const result = await controller.submitDelete(reservationId);
          if (result.ok && onDeleted) onDeleted();
        }
      });
    }
  }

  render();
  return controller;
}
