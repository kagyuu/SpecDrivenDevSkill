// 共通APIクライアント。docs/02-frontend-spec.md 2章の外部仕様に対応。
// Cookie経由のセッションを送信するため credentials: "include" を用いる。

const BASE = "";

async function request(method, path, body) {
  const res = await fetch(BASE + path, {
    method,
    credentials: "include",
    headers: body ? { "Content-Type": "application/json" } : {},
    body: body ? JSON.stringify(body) : undefined,
  });
  let data = null;
  if (res.status !== 204) {
    try {
      data = await res.json();
    } catch (e) {
      data = null;
    }
  }
  if (!res.ok) {
    const err = new Error((data && data.error && data.error.message) || `HTTP ${res.status}`);
    err.status = res.status;
    err.body = data;
    throw err;
  }
  return data;
}

export const api = {
  login: (employee_id, password) => request("POST", "/api/auth/login", { employee_id, password }),
  logout: () => request("POST", "/api/auth/logout"),
  me: () => request("GET", "/api/me"),
  listRooms: (includeInactive) =>
    request("GET", `/api/rooms${includeInactive ? "?include_inactive=true" : ""}`),
  createRoom: (payload) => request("POST", "/api/rooms", payload),
  updateRoom: (id, payload) => request("PUT", `/api/rooms/${id}`, payload),
  deleteRoom: (id) => request("DELETE", `/api/rooms/${id}`),
  listReservations: (dateFrom, dateTo, roomId) =>
    request(
      "GET",
      `/api/reservations?date_from=${dateFrom}&date_to=${dateTo}${roomId ? `&room_id=${roomId}` : ""}`
    ),
  listMyReservations: (period) => request("GET", `/api/reservations/mine?period=${period || "future"}`),
  getReservation: (id) => request("GET", `/api/reservations/${id}`),
  createReservation: (payload) => request("POST", "/api/reservations", payload),
  updateReservation: (id, payload) => request("PUT", `/api/reservations/${id}`, payload),
  deleteReservation: (id) => request("DELETE", `/api/reservations/${id}`),
  listUsers: () => request("GET", "/api/users"),
  createUser: (payload) => request("POST", "/api/users", payload),
  updateUser: (id, payload) => request("PUT", `/api/users/${id}`, payload),
  deleteUser: (id) => request("DELETE", `/api/users/${id}`),
};
