// S05 マイ予約一覧画面 (docs/P002-frontend-spec.md §3 S05)
// 期間フィルタ(upcoming/past)の既定値はupcoming。

export function createMyReservationsController(reservationApi) {
  const state = { reservations: [], period: "upcoming" };
  return {
    getState() {
      return state;
    },
    async load(period = "upcoming") {
      state.period = period;
      state.reservations = await reservationApi.getMine(period);
      return state.reservations;
    },
  };
}

export function mountMyReservationsPage(container, reservationApi) {
  const controller = createMyReservationsController(reservationApi);

  async function render(period = "upcoming") {
    await controller.load(period);
    const state = controller.getState();
    container.innerHTML = `
      <h2>マイ予約一覧</h2>
      <div class="form-row">
        <label>期間</label>
        <select id="period-select">
          <option value="upcoming" ${period === "upcoming" ? "selected" : ""}>今後の予約</option>
          <option value="past" ${period === "past" ? "selected" : ""}>過去の予約</option>
        </select>
      </div>
      <table>
        <thead><tr><th>日付</th><th>時間</th><th>件名</th></tr></thead>
        <tbody>
          ${state.reservations.map((r) => `
            <tr>
              <td>${r.date}</td><td>${r.start_time}-${r.end_time}</td>
              <td><a href="#/reservations/${r.id}">${r.title}</a></td>
            </tr>`).join("")}
        </tbody>
      </table>
    `;
    container.querySelector("#period-select").addEventListener("change", (e) => {
      render(e.target.value);
    });
  }

  render();
  return controller;
}
