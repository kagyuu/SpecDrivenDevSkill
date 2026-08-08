// T010 — S06・S07画面とマスタAPIの接続(docs/P008-test-direction/T010-master-screens-api.md)
// 実サーバー(uvicorn)に対して実行する。
import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import { installDom } from '../helpers/dom-env.js';
import { startServer, makeFetch } from '../helpers/server.js';
import * as api from '../../src/lib/api.js';

let server;
let httpFetch;
let s06;
let s07;
let env;

async function callJson(path, method, body) {
  const options = { method, headers: { 'Content-Type': 'application/json' } };
  if (body) options.body = JSON.stringify(body);
  return httpFetch(path, options);
}

before(async () => {
  server = await startServer();
  httpFetch = makeFetch(server.baseUrl);
  // 事前準備: 基準データセット(ユーザー4件・会議室2件(うち1件無効))を実APIで投入する
  assert.equal((await callJson('/api/auth/login', 'POST', { user_id: 'admin001', password: 'Passw0rd!23' })).status, 200);
  for (const user of [
    { user_id: 'user001', name: '山田 太郎', role: 'general', password: 'Passw0rd!23' },
    { user_id: 'user002', name: '鈴木 花子', role: 'general', password: 'Passw0rd!23' },
    { user_id: 'user003', name: '退職 次郎', role: 'general', password: 'Passw0rd!23', is_active: false },
  ]) {
    assert.equal((await callJson('/api/users', 'POST', user)).status, 201);
  }
  assert.equal((await callJson('/api/rooms', 'POST', { name: '会議室A', capacity: 10, equipment: 'プロジェクタ', description: '窓側の大会議室' })).status, 201);
  assert.equal((await callJson('/api/rooms', 'POST', { name: '会議室C', capacity: 20, is_active: false })).status, 201);

  env = installDom();
  api.runtime.fetch = httpFetch;
  api.runtime.navigate = (hash) => { globalThis.location.hash = hash; };
  globalThis.confirm = () => true;
  s06 = await import('../../src/views/s06-room-admin.js');
  s07 = await import('../../src/views/s07-user-admin.js');
});

after(() => { if (server) server.stop(); });

test('手順1: S06に会議室2件が描画され、無効行に is-inactive・説明文の列がある', async () => {
  const root = await s06.render({}, env.app, env.header);
  const rows = root.querySelectorAll('[data-role="room-rows"] tr');
  assert.equal(rows.length, 2);
  assert.equal(rows[0].className, '');
  assert.equal(rows[1].className, 'is-inactive');
  assert.equal(rows[0].querySelector('[data-column="description"]').textContent, '窓側の大会議室');
  // 管理者のヘッダーには管理メニューが出る
  assert.ok(env.header.querySelector('[href="#/admin/rooms"]'));
});

test('手順2: S06のフォームから新規登録すると一覧に1件増える', async () => {
  const root = env.app.querySelector('[data-view="s06-room-admin"]');
  root.querySelector('[data-action="new"]').click();
  const form = root.querySelector('[data-role="room-form"]');
  form.querySelector('[name="name"]').value = '会議室B';
  form.querySelector('[name="capacity"]').value = '4';
  form.querySelector('[name="equipment"]').value = '';
  form.querySelector('[name="description"]').value = '';
  assert.equal(await s06.submit(env.app), true);
  assert.equal(env.app.querySelectorAll('[data-role="room-rows"] tr').length, 3);
});

test('手順3: 編集すると PUT の内容が一覧に反映される', async () => {
  const rows = env.app.querySelectorAll('[data-role="room-rows"] tr');
  const target = rows[rows.length - 1];
  target.querySelector('[data-action="edit"]').click();
  const form = env.app.querySelector('[data-role="room-form"]');
  form.querySelector('[name="capacity"]').value = '6';
  form.querySelector('[name="description"]').value = '小会議室';
  assert.equal(await s06.submit(env.app), true);
  const updated = env.app.querySelectorAll('[data-role="room-rows"] tr');
  const last = updated[updated.length - 1];
  assert.equal(last.querySelector('[data-column="description"]').textContent, '小会議室');
});

test('手順4: 同名で再登録すると会議室名欄の直下に409のメッセージが出る', async () => {
  const root = env.app.querySelector('[data-view="s06-room-admin"]');
  root.querySelector('[data-action="new"]').click();
  const form = root.querySelector('[data-role="room-form"]');
  form.querySelector('[name="name"]').value = '会議室A';
  form.querySelector('[name="capacity"]').value = '10';
  assert.equal(await s06.submit(env.app), false);
  assert.equal(
    env.app.querySelector('[data-error-for="name"]').textContent,
    '同じ名前の会議室がすでに登録されています。'
  );
});

test('手順5: S07へ遷移するとユーザー4件と「戻る」リンクが描画される', async () => {
  assert.ok(env.app.querySelector('[data-link="users"]'), 'S06にユーザー管理リンクがある');
  const root = await s07.render({}, env.app, env.header);
  assert.equal(root.querySelectorAll('[data-role="user-rows"] tr').length, 4);
  assert.ok(root.querySelector('[data-link="back"]'));
});

test('手順6: 自分自身の削除は画面上部にAPIの message が出て一覧は変わらない', async () => {
  const before = env.app.querySelectorAll('[data-role="user-rows"] tr').length;
  assert.equal(await s07.remove(env.app, 'admin001'), false);
  assert.equal(
    env.app.querySelector('[data-top-message]').textContent,
    '自分自身を無効化することはできません。'
  );
  assert.equal(env.app.querySelectorAll('[data-role="user-rows"] tr').length, before);
});

test('手順7: 一般ユーザーで #/admin/rooms を開くと権限メッセージのみ・ヘッダーに管理リンクなし', async () => {
  await api.post('/api/auth/logout');
  httpFetch.clearCookies();
  const login = await api.post('/api/auth/login', { user_id: 'user001', password: 'Passw0rd!23' });
  assert.equal(login.user.role, 'general');
  const root = await s06.render({}, env.app, env.header);
  assert.equal(root.querySelector('[data-role="room-list"]'), null);
  assert.equal(
    root.querySelector('[data-permission-message]').textContent,
    'この画面を表示する権限がありません。'
  );
  assert.equal(env.header.querySelector('[href="#/admin/rooms"]'), null);
  assert.equal(env.header.querySelector('[href="#/admin/users"]'), null);
});
