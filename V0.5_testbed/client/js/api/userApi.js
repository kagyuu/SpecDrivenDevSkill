// ユーザーAPI fetchラッパー (docs/P002-frontend-spec.md §4.14〜§4.17)

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

export async function list(includeInactive = true) {
  const query = includeInactive ? "" : "?include_inactive=false";
  const response = await fetch(`/api/users${query}`, { credentials: "include" });
  const body = await parseJsonSafe(response);
  if (!response.ok) throw toAppError(body, response.status);
  return body.users;
}

export async function create(data) {
  const response = await fetch("/api/users", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(data),
  });
  const body = await parseJsonSafe(response);
  if (!response.ok) throw toAppError(body, response.status);
  return body;
}

export async function update(userId, data) {
  const response = await fetch(`/api/users/${userId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(data),
  });
  const body = await parseJsonSafe(response);
  if (!response.ok) throw toAppError(body, response.status);
  return body;
}

export async function remove(userId) {
  const response = await fetch(`/api/users/${userId}`, { method: "DELETE", credentials: "include" });
  const body = await parseJsonSafe(response);
  if (!response.ok) throw toAppError(body, response.status);
  return body;
}
