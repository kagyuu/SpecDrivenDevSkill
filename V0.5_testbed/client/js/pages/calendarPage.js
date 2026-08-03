// S02 予約カレンダー画面 (docs/P002-frontend-spec.md §3 S02, §6.3)
// 9:00〜18:00を30分刻みで表示する。

const SLOT_START_MINUTES = 9 * 60;
const SLOT_END_MINUTES = 18 * 60;
const SLOT_STEP_MINUTES = 30;

function minutesToHHMM(minutes) {
  const h = String(Math.floor(minutes / 60)).padStart(2, "0");
  const m = String(minutes % 60).padStart(2, "0");
  return `${h}:${m}`;
}

function hhmmToMinutes(hhmm) {
  const [h, m] = hhmm.split(":").map(Number);
  return h * 60 + m;
}

/** 9:00〜18:00、30分刻みの時間帯一覧を返す(18スロット)。 */
export function generateTimeSlots() {
  const slots = [];
  for (let t = SLOT_START_MINUTES; t < SLOT_END_MINUTES; t += SLOT_STEP_MINUTES) {
    slots.push(minutesToHHMM(t));
  }
  return slots;
}

/**
 * 会議室×時間帯グリッドを構築する(DOM非依存、unit test対象)。
 * @param {Array} rooms [{id, name}, ...]
 * @param {Array} reservations [{room_id, start_time, end_time, title, created_by}, ...]
 * @returns {Array} [{room, slots: [{time, booked, reservation}]}]
 */
export function buildCalendarGrid(rooms, reservations) {
  const slots = generateTimeSlots();
  return rooms.map((room) => {
    const roomReservations = reservations.filter((r) => r.room_id === room.id);
    return {
      room,
      slots: slots.map((time) => {
        const slotStart = hhmmToMinutes(time);
        const slotEnd = slotStart + SLOT_STEP_MINUTES;
        const match = roomReservations.find((r) => {
          const start = hhmmToMinutes(r.start_time);
          const end = hhmmToMinutes(r.end_time);
          return slotStart < end && slotEnd > start;
        });
        return { time, booked: Boolean(match), reservation: match || null };
      }),
    };
  });
}

export function createCalendarController(roomApi, reservationApi) {
  const state = { rooms: [], reservations: [], grid: [] };
  return {
    getState() {
      return state;
    },
    async load(dateFrom, dateTo) {
      state.rooms = await roomApi.list();
      state.reservations = await reservationApi.listReservations(dateFrom, dateTo);
      state.grid = buildCalendarGrid(state.rooms, state.reservations);
      return state.grid;
    },
  };
}

export function mountCalendarPage(container, roomApi, reservationApi) {
  const controller = createCalendarController(roomApi, reservationApi);
  const today = new Date().toISOString().slice(0, 10);

  async function render() {
    await controller.load(today, today);
    const state = controller.getState();
    const slotHeaders = generateTimeSlots().map((t) => `<th>${t}</th>`).join("");
    const rows = state.grid.map(({ room, slots }) => `
      <tr>
        <td>${room.name}</td>
        ${slots.map((s) => `<td class="${s.booked ? "slot-booked" : "slot-free"}" title="${s.reservation ? s.reservation.title : ""}"></td>`).join("")}
      </tr>
    `).join("");
    container.innerHTML = `
      <h2>予約カレンダー(${today})</h2>
      <table class="grid-table"><thead><tr><th>会議室</th>${slotHeaders}</tr></thead><tbody>${rows}</tbody></table>
    `;
  }

  render();
  return controller;
}
