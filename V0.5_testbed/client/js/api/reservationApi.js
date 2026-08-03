// 予約API fetchラッパー (docs/P002-frontend-spec.md §4.8〜§4.13)
// U003-6: listReservations, createReservation
// U004-5: getDetail, getMine, update, remove

async function parseJsonSafe(response) {
  try {
    return await response.json();
  } catch (e) {
    return null;
  }
}

function toAppError(body, status) {
  const error = new Error(body?.error?.message || "リクエストに失敗しました");
  error.code = body?.error?.code;
  error.status = status;
  error.details = body?.error?.details;
  return error;
}

export async function listReservations(dateFrom, dateTo, roomIds) {
  const params = new URLSearchParams({ date_from: dateFrom, date_to: dateTo });
  if (roomIds && roomIds.length) params.set("room_ids", roomIds.join(","));
  const response = await fetch(`/api/reservations?${params.toString()}`, { credentials: "include" });
  const body = await parseJsonSafe(response);
  if (!response.ok) throw toAppError(body, response.status);
  return body.reservations;
}

export async function createReservation(data) {
  const response = await fetch("/api/reservations", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(data),
  });
  const body = await parseJsonSafe(response);
  if (!response.ok) throw toAppError(body, response.status);
  return body;
}

export async function getDetail(reservationId) {
  const response = await fetch(`/api/reservations/${reservationId}`, { credentials: "include" });
  const body = await parseJsonSafe(response);
  if (!response.ok) throw toAppError(body, response.status);
  return body;
}

export async function getMine(period = "upcoming") {
  const response = await fetch(`/api/reservations/mine?period=${period}`, { credentials: "include" });
  const body = await parseJsonSafe(response);
  if (!response.ok) throw toAppError(body, response.status);
  return body.reservations;
}

export async function update(reservationId, data) {
  const response = await fetch(`/api/reservations/${reservationId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(data),
  });
  const body = await parseJsonSafe(response);
  if (!response.ok) throw toAppError(body, response.status);
  return body;
}

export async function remove(reservationId) {
  const response = await fetch(`/api/reservations/${reservationId}`, {
    method: "DELETE",
    credentials: "include",
  });
  const body = await parseJsonSafe(response);
  if (!response.ok) throw toAppError(body, response.status);
  return body;
}
