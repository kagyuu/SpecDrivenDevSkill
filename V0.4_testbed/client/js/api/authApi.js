// 認証API fetchラッパー (docs/P002-frontend-spec.md §4.1〜§4.3)
// credentials: "include" によりCookieベース認証(ADR-004)のCookieを送受信する。

const BASE_URL = "";

async function parseJsonSafe(response) {
  try {
    return await response.json();
  } catch (e) {
    return null;
  }
}

export async function login(employeeId, password) {
  const response = await fetch(`${BASE_URL}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({ employee_id: employeeId, password }),
  });
  const body = await parseJsonSafe(response);
  if (!response.ok) {
    const error = new Error(body?.error?.message || "ログインに失敗しました");
    error.code = body?.error?.code;
    error.status = response.status;
    throw error;
  }
  return body.user;
}

export async function logout() {
  const response = await fetch(`${BASE_URL}/api/auth/logout`, {
    method: "POST",
    credentials: "include",
  });
  return parseJsonSafe(response);
}

export async function getMe() {
  const response = await fetch(`${BASE_URL}/api/me`, {
    method: "GET",
    credentials: "include",
  });
  const body = await parseJsonSafe(response);
  if (!response.ok) {
    const error = new Error(body?.error?.message || "認証が必要です");
    error.code = body?.error?.code;
    error.status = response.status;
    throw error;
  }
  return body.user;
}
