// U002-T4 単体テスト — S06 会議室管理画面(P002 3.6 / 2.3 / 2.4)
import { test, beforeEach } from 'node:test';
import assert from 'node:assert/strict';
import { installDom } from './helpers/dom-env.js';
import * as api from '../src/lib/api.js';

let s06;
let app;
let calls;
let responses;

const ADMIN = { user_id: 'admin001', name: '初期管理者', role: 'admin' };
const GENERAL = { user_id: 'user001', name: '山田 太郎', role: 'general' };
const ROOMS = [
  { room_id: 1, name: '会議室A', capacity: 10, equipment: 'プロジェクタ', description: '窓側の大会議室', is_active: true },
  { room_id: 2, name: '会議室B', capacity: 4, equipment: '', description: '', is_active: true },
  { room_id: 3, name: '会議室C', capacity: 6, equipment: '', description: '', is_active: false },
];

beforeEach(async () => {
  app = installDom().app;
  calls = [];
  responses = {};
  api.runtime.navigate = (hash) => { globalThis.location.hash = hash; };
  api.runtime.fetch = async (path, options) => {
    calls.push({ path, method: options.method, body: options.body ? JSON.parse(options.body) : null });
    const key = `${options.method} ${path}`;
    const canned = responses[key];
    if (canned) return canned;
    if (path.startsWith('/api/rooms')) return { status: 200, json: async () => ({ rooms: ROOMS }) };
    if (path === '/api/me') return { status: 200, json: async () => ({ user: ADMIN }) };
    return { status: 204, json: async () => null };
  };
  api.takePendingMessage();
  s06 = await import('../src/views/s06-room-admin.js');
});

function errorResponse(status, code, message) {
  return { status, json: async () => ({ error: { code, message } }) };
}

function fillForm(root, values) {
  const form = root.querySelector('[data-role="room-form"]');
  for (const [name, value] of Object.entries(values)) {
    const input = form.querySelector(`[name="${name}"]`);
    if (name === 'is_active') input.checked = value;
    else input.value = value;
  }
  return form;
}

test('一覧: 3件描画され、無効行に is-inactive が付き、説明文の列がある', () => {
  const root = s06.view(app, ADMIN, ROOMS);
  const rows = root.querySelectorAll('[data-role="room-rows"] tr');
  assert.equal(rows.length, 3);
  assert.equal(rows[0].className, '');
  assert.equal(rows[2].className, 'is-inactive');
  assert.equal(rows[0].querySelector('[data-column="description"]').textContent, '窓側の大会議室');
  assert.ok(root.querySelector('[data-link="users"]'), 'ユーザー管理リンクがある');
});

test('新規登録: POST /api/rooms が正しいボディで呼ばれる', async () => {
  const root = s06.view(app, ADMIN, ROOMS);
  fillForm(root, { room_id: '', name: '会議室D', capacity: '8', equipment: 'TV', description: '小部屋', is_active: true });
  assert.equal(await s06.submit(app), true);
  const post = calls.find((c) => c.method === 'POST');
  assert.equal(post.path, '/api/rooms');
  assert.deepEqual(post.body, { name: '会議室D', capacity: 8, equipment: 'TV', description: '小部屋', is_active: true });
});

test('編集: PUT /api/rooms/{id} が呼ばれる', async () => {
  const root = s06.view(app, ADMIN, ROOMS);
  root.querySelectorAll('[data-action="edit"]')[0].click();
  const form = root.querySelector('[data-role="room-form"]');
  assert.equal(form.querySelector('[name="name"]').value, '会議室A');
  form.querySelector('[name="capacity"]').value = '12';
  await s06.submit(app);
  const put = calls.find((c) => c.method === 'PUT');
  assert.equal(put.path, '/api/rooms/1');
  assert.equal(put.body.capacity, 12);
});

test('削除: 確認OKで DELETE、キャンセルで呼ばれない', async () => {
  const root = s06.view(app, ADMIN, ROOMS);
  globalThis.confirm = () => false;
  await s06.remove(app, 1);
  assert.equal(calls.filter((c) => c.method === 'DELETE').length, 0);
  globalThis.confirm = () => true;
  await s06.remove(app, 1);
  assert.equal(calls.filter((c) => c.method === 'DELETE')[0].path, '/api/rooms/1');
  assert.ok(root);
});

test('権限: 一般ユーザーには表を描画せず権限メッセージのみ', () => {
  const root = s06.view(app, GENERAL, ROOMS);
  assert.equal(root.querySelector('[data-role="room-list"]'), null);
  assert.equal(root.querySelector('[data-permission-message]').textContent, 'この画面を表示する権限がありません。');
});

test('409 DUPLICATE_KEY: 会議室名欄の直下にメッセージが出る', async () => {
  const root = s06.view(app, ADMIN, ROOMS);
  responses['POST /api/rooms'] = errorResponse(409, 'DUPLICATE_KEY', '同じ名前の会議室がすでに登録されています。');
  fillForm(root, { room_id: '', name: '会議室A', capacity: '10', equipment: '', description: '', is_active: true });
  assert.equal(await s06.submit(app), false);
  assert.equal(
    app.querySelector('[data-error-for="name"]').textContent,
    '同じ名前の会議室がすでに登録されています。'
  );
});

test('409 CONSTRAINT_VIOLATION: 画面上部にAPIの message が出る', async () => {
  s06.view(app, ADMIN, ROOMS);
  responses['DELETE /api/rooms/1'] = errorResponse(
    409, 'CONSTRAINT_VIOLATION', 'この会議室には今後の予約が2件あります。先に予約を取り消してください。'
  );
  globalThis.confirm = () => true;
  assert.equal(await s06.remove(app, 1), false);
  assert.equal(
    app.querySelector('[data-top-message]').textContent,
    'この会議室には今後の予約が2件あります。先に予約を取り消してください。'
  );
});

test('収容人数0: APIを呼ばずエラー表示', async () => {
  const root = s06.view(app, ADMIN, ROOMS);
  fillForm(root, { room_id: '', name: '会議室D', capacity: '0', equipment: '', description: '', is_active: true });
  assert.equal(await s06.submit(app), false);
  assert.equal(calls.length, 0);
  assert.equal(
    root.querySelector('[data-error-for="capacity"]').textContent,
    '収容人数は1以上500以下の整数で入力してください。'
  );
});
