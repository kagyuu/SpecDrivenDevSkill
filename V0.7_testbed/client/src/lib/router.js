// ハッシュルーティング(P002 2.2)。
// ルート定義は「パス → モジュールの描画関数」の登録テーブル。画面追加時は ROUTES に1行足す。

const routes = [];

// 画面モジュールは動的 import で読み込む(views → router の循環参照を避けるため)。
// P002 2.2 のルーティング表(7ルート)。`/reservations/new` は `/reservations/{id}` より先に置く。
export const ROUTES = [
  { path: '/login', load: () => import('../views/s01-login.js') },
  { path: '/calendar', load: () => import('../views/s02-calendar.js') },
  { path: '/reservations/new', load: () => import('../views/s03-reservation-new.js') },
  {
    path: '/reservations/{reservation_id}',
    load: () => import('../views/s04-reservation-detail.js'),
  },
  { path: '/my-reservations', load: () => import('../views/s05-my-reservations.js') },
  { path: '/admin/rooms', load: () => import('../views/s06-room-admin.js') },
  { path: '/admin/users', load: () => import('../views/s07-user-admin.js') },
];

export function register(pattern, render) {
  routes.push({ pattern, render, matcher: toMatcher(pattern) });
}

export function registerLazy(pattern, load) {
  register(pattern, async (params) => (await load()).render(params));
}

export function defineDefaultRoutes() {
  reset();
  for (const route of ROUTES) registerLazy(route.path, route.load);
}

function toMatcher(pattern) {
  const names = [];
  const source = pattern.replace(/\{(\w+)\}/g, (_, name) => {
    names.push(name);
    return '([^/]+)';
  });
  return { regexp: new RegExp(`^${source}$`), names };
}

// `#/reservations/new?room_id=1&date=...` のクエリ部分をパラメータとして取り出す(P002 3.2 → 3.3)。
export function parseQuery(text) {
  const params = {};
  for (const pair of String(text || '').split('&')) {
    if (!pair) continue;
    const index = pair.indexOf('=');
    const key = index < 0 ? pair : pair.slice(0, index);
    const value = index < 0 ? '' : pair.slice(index + 1);
    params[decodeURIComponent(key)] = decodeURIComponent(value);
  }
  return params;
}

export function resolve(hash) {
  const raw = (hash || '').replace(/^#/, '') || '/login';
  const queryAt = raw.indexOf('?');
  const path = queryAt < 0 ? raw : raw.slice(0, queryAt);
  const query = queryAt < 0 ? {} : parseQuery(raw.slice(queryAt + 1));
  for (const route of routes) {
    const found = route.matcher.regexp.exec(path);
    if (found) {
      const params = { ...query };
      route.matcher.names.forEach((name, index) => {
        params[name] = decodeURIComponent(found[index + 1]);
      });
      return { route, params };
    }
  }
  return null;
}

export function navigate(hash) {
  if (globalThis.location) globalThis.location.hash = hash;
}

export async function renderCurrent() {
  const hash = globalThis.location ? globalThis.location.hash : '';
  const matched = resolve(hash);
  if (!matched) {
    navigate('#/calendar'); // 未知のハッシュは #/calendar へ(P002 2.2)
    return;
  }
  await matched.route.render(matched.params);
}

export function start() {
  globalThis.addEventListener('hashchange', () => {
    renderCurrent();
  });
  return renderCurrent();
}

export function reset() {
  routes.length = 0;
}
