// 会議室API fetchラッパー (docs/P002-frontend-spec.md §4.4〜§4.7)

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

export async function list(includeInactive = false) {
  const query = includeInactive ? "?include_inactive=true" : "";
  const response = await fetch(`/api/rooms${query}`, { credentials: "include" });
  const body = await parseJsonSafe(response);
  if (!response.ok) throw toAppError(body, response.status);
  return body.rooms;
}

export async function create(data) {
  const response = await fetch("/api/rooms", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(data),
  });
  const body = await parseJsonSafe(response);
  if (!response.ok) throw toAppError(body, response.status);
  return body;
}

export async function update(roomId, data) {
  const response = await fetch(`/api/rooms/${roomId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(data),
  });
  const body = await parseJsonSafe(response);
  if (!response.ok) throw toAppError(body, response.status);
  return body;
}

export async function remove(roomId) {
  const response = await fetch(`/api/rooms/${roomId}`, { method: "DELETE", credentials: "include" });
  const body = await parseJsonSafe(response);
  if (!response.ok) throw toAppError(body, response.status);
  return body;
}
