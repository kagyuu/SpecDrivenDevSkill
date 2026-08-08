// APIクライアント(P002 5.1 / 5.2 / 2.4)。同一オリジン配信のためCORSは考慮しない(ADR-010)。

export const SESSION_EXPIRED_MESSAGE = 'セッションの有効期限が切れました。再度ログインしてください。';

// テストから差し替えられるようにした実行時の依存(fetch / 画面遷移)。
export const runtime = {
  fetch: (...args) => globalThis.fetch(...args),
  navigate: (hash) => {
    if (globalThis.location) globalThis.location.hash = hash;
  },
};

let pendingMessage = null;

// 401 UNAUTHENTICATED でS01へ戻したときのメッセージを1回だけ取り出す(P002 2.4)。
export function takePendingMessage() {
  const message = pendingMessage;
  pendingMessage = null;
  return message;
}

const DEFAULT_MESSAGES = {
  FORBIDDEN: 'この操作を行う権限がありません。',
  NOT_FOUND: '対象のデータが見つかりません。削除された可能性があります。',
  INTERNAL_ERROR: 'システムエラーが発生しました。時間をおいて再度お試しください。',
};

export class ApiClientError extends Error {
  constructor({ status, code, message, details, extra }) {
    super(message);
    this.name = 'ApiClientError';
    this.status = status;
    this.code = code;
    this.message = message;
    this.details = details || [];
    this.extra = extra || {};
  }
}

function toError(status, payload) {
  const error = (payload && payload.error) || {};
  const code = error.code || (status >= 500 ? 'INTERNAL_ERROR' : 'UNKNOWN_ERROR');
  const extra = {};
  for (const [key, value] of Object.entries(error)) {
    if (key !== 'code' && key !== 'message' && key !== 'details') extra[key] = value;
  }
  return new ApiClientError({
    status,
    code,
    message: error.message || DEFAULT_MESSAGES[code] || 'エラーが発生しました。',
    details: error.details || [],
    extra,
  });
}

async function request(method, path, body) {
  const options = {
    method,
    credentials: 'same-origin',
    headers: { 'Content-Type': 'application/json' },
  };
  if (body !== undefined && body !== null) options.body = JSON.stringify(body);

  const response = await runtime.fetch(path, options);
  const status = response.status;
  if (status === 204) return null;

  let payload = null;
  try {
    payload = await response.json();
  } catch (e) {
    payload = null;
  }
  if (status >= 200 && status < 300) return payload;

  const error = toError(status, payload);
  // セッション切れのみS01へ戻す。ログイン失敗(AUTH_FAILED)はS01が自分で表示する(P002 2.4 / 3.1)
  if (status === 401 && error.code === 'UNAUTHENTICATED') {
    pendingMessage = SESSION_EXPIRED_MESSAGE;
    runtime.navigate('#/login');
  }
  throw error;
}

export const get = (path) => request('GET', path);
export const post = (path, body) => request('POST', path, body);
export const put = (path, body) => request('PUT', path, body);
export const del = (path) => request('DELETE', path);
