// U004-T5 単体テスト — router.js / header.js(P002 2.2 / 2.3 / 4)
import { test, beforeEach } from 'node:test';
import assert from 'node:assert/strict';
import { installDom } from './helpers/dom-env.js';
import * as router from '../src/lib/router.js';
import { renderHeader } from '../src/components/header.js';
import * as api from '../src/lib/api.js';

const ADMIN = { user_id: 'admin001', name: '管理 太郎', role: 'admin' };
const GENERAL = { user_id: 'user001', name: '山田 太郎', role: 'general' };

let env;
let calls;

beforeEach(() => {
  env = installDom();
  calls = [];
  api.runtime.navigate = (hash) => { globalThis.location.hash = hash; };
  api.runtime.fetch = async (path, options) => {
    calls.push({ path, method: options.method });
    if (path === '/api/me') return { status: 200, json: async () => ({ user: GENERAL }) };
    return { status: 204, json: async () => null };
  };
  api.takePendingMessage();
  router.reset();
});

const PATHS = [
  '/login',
  '/calendar',
  '/reservations/new',
  '/reservations/{reservation_id}',
  '/my-reservations',
  '/admin/rooms',
  '/admin/users',
];

test('ROUTES: P002 2.2 の7ルートがこの順で登録されている', () => {
  assert.deepEqual(router.ROUTES.map((r) => r.path), PATHS);
});

test('ROUTES: 各ルートのモジュールが render をエクスポートしている', async () => {
  for (const route of router.ROUTES) {
    const module = await route.load();
    assert.equal(typeof module.render, 'function', route.path);
  }
});

test('7つのハッシュそれぞれで、対応する描画関数が1回だけ呼ばれる', async () => {
  const rendered = [];
  for (const path of PATHS) {
    router.register(path, () => { rendered.push(path); });
  }
  const hashes = [
    ['#/login', '/login'],
    ['#/calendar', '/calendar'],
    ['#/reservations/new', '/reservations/new'],
    ['#/reservations/12', '/reservations/{reservation_id}'],
    ['#/my-reservations', '/my-reservations'],
    ['#/admin/rooms', '/admin/rooms'],
    ['#/admin/users', '/admin/users'],
  ];
  for (const [hash, expected] of hashes) {
    rendered.length = 0;
    globalThis.location.hash = hash;
    await router.renderCurrent();
    assert.deepEqual(rendered, [expected], hash);
  }
});

test('パラメータ付きルート: #/reservations/12 で reservation_id=12 が渡る', async () => {
  let params = null;
  for (const path of PATHS) router.register(path, (p) => { params = p; });
  globalThis.location.hash = '#/reservations/12';
  await router.renderCurrent();
  assert.equal(params.reservation_id, '12');
});

test('#/reservations/new はIDルートより先にマッチする', () => {
  for (const path of PATHS) router.register(path, () => {});
  assert.equal(router.resolve('#/reservations/new').route.pattern, '/reservations/new');
});

test('クエリ付きハッシュがパラメータとして渡る', () => {
  for (const path of PATHS) router.register(path, () => {});
  const matched = router.resolve('#/reservations/new?room_id=2&date=2026-08-10&start=14:00');
  assert.equal(matched.route.pattern, '/reservations/new');
  assert.equal(matched.params.room_id, '2');
  assert.equal(matched.params.date, '2026-08-10');
  assert.equal(matched.params.start, '14:00');
});

test('未知のハッシュ(#/unknown)は #/calendar にリダイレクトされる', async () => {
  for (const path of PATHS) router.register(path, () => {});
  globalThis.location.hash = '#/unknown';
  await router.renderCurrent();
  assert.equal(globalThis.location.hash, '#/calendar');
});

test('ヘッダー: 管理者は4リンク、一般ユーザーは2リンク', () => {
  const adminLinks = renderHeader(env.header, ADMIN).querySelectorAll('a');
  assert.deepEqual(adminLinks.map((a) => a.getAttribute('href')), [
    '#/calendar', '#/my-reservations', '#/admin/rooms', '#/admin/users',
  ]);
  const generalLinks = renderHeader(env.header, GENERAL).querySelectorAll('a');
  assert.deepEqual(generalLinks.map((a) => a.getAttribute('href')), [
    '#/calendar', '#/my-reservations',
  ]);
});

test('ヘッダー: ログアウトでAPIが呼ばれ #/login へ遷移する', async () => {
  const header = renderHeader(env.header, GENERAL);
  await header.querySelector('[data-action="logout"]').click();
  assert.ok(calls.some((c) => c.path === '/api/auth/logout' && c.method === 'POST'));
  assert.equal(globalThis.location.hash, '#/login');
});

test('GET /api/me が401のとき、どのルートでも #/login へ遷移する', async () => {
  api.runtime.fetch = async (path, options) => {
    calls.push({ path, method: options.method });
    return {
      status: 401,
      json: async () => ({ error: { code: 'UNAUTHENTICATED', message: 'セッション切れ' } }),
    };
  };
  for (const name of ['s02-calendar', 's05-my-reservations']) {
    globalThis.location.hash = '';
    const module = await import(`../src/views/${name}.js`);
    await assert.rejects(() => module.render({}, env.app, env.header));
    assert.equal(globalThis.location.hash, '#/login', name);
  }
});

test('一般ユーザーが #/admin/rooms を直接開くと権限メッセージのみが表示される', async () => {
  const s06 = await import('../src/views/s06-room-admin.js');
  const root = await s06.render({}, env.app, env.header);
  assert.equal(
    root.querySelector('[data-permission-message]').textContent,
    'この画面を表示する権限がありません。'
  );
  assert.equal(root.querySelector('[data-role="room-list"]'), null);
});

test('S01以外の画面は描画前に GET /api/me を呼ぶ', async () => {
  const views = ['s02-calendar', 's05-my-reservations', 's06-room-admin', 's07-user-admin'];
  api.runtime.fetch = async (path, options) => {
    calls.push({ path, method: options.method });
    if (path === '/api/me') return { status: 200, json: async () => ({ user: GENERAL }) };
    if (path.startsWith('/api/rooms')) return { status: 200, json: async () => ({ rooms: [] }) };
    if (path.startsWith('/api/users')) return { status: 200, json: async () => ({ users: [] }) };
    if (path.startsWith('/api/reservations')) {
      return { status: 200, json: async () => ({ reservations: [] }) };
    }
    return { status: 204, json: async () => null };
  };
  for (const name of views) {
    calls.length = 0;
    const module = await import(`../src/views/${name}.js`);
    await module.render({}, env.app, env.header);
    assert.equal(calls[0].path, '/api/me', name);
  }
  // S01 は /api/me を呼ばない(P002 2.2)
  calls.length = 0;
  const s01 = await import('../src/views/s01-login.js');
  s01.render({}, env.app, env.header);
  assert.equal(calls.length, 0);
});
