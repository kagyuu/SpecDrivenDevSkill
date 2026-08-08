// T003 — S01ログイン画面とログインAPIの接続(docs/P008-test-direction/T003-s01-login-api.md)
// 実サーバー(uvicorn)に対して実行する。
import { test, before, after, beforeEach } from 'node:test';
import assert from 'node:assert/strict';
import { installDom } from '../helpers/dom-env.js';
import { startServer, makeFetch } from '../helpers/server.js';
import * as api from '../../src/lib/api.js';

let server;
let httpFetch;
let s01;
let app;

before(async () => {
  server = await startServer();
  httpFetch = makeFetch(server.baseUrl);
  // 事前準備: 基準データセットのユーザーを実APIで投入する
  const login = await httpFetch('/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id: 'admin001', password: 'Passw0rd!23' }),
  });
  assert.equal(login.status, 200);
  for (const user of [
    { user_id: 'user001', name: '山田 太郎', role: 'general', password: 'Passw0rd!23' },
    { user_id: 'user002', name: '鈴木 花子', role: 'general', password: 'Passw0rd!23' },
    { user_id: 'user003', name: '退職 次郎', role: 'general', password: 'Passw0rd!23', is_active: false },
  ]) {
    const res = await httpFetch('/api/users', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(user),
    });
    assert.equal(res.status, 201, `${user.user_id} の投入`);
  }
  httpFetch.clearCookies();
  s01 = await import('../../src/views/s01-login.js');
});

after(() => { if (server) server.stop(); });

beforeEach(() => {
  app = installDom().app;
  httpFetch.clearCookies();
  api.runtime.fetch = httpFetch;
  api.runtime.navigate = (hash) => { globalThis.location.hash = hash; };
  api.takePendingMessage();
});

function fill(form, userId, password) {
  form.querySelector('[name="user_id"]').value = userId;
  form.querySelector('[name="password"]').value = password;
}

test('手順1: S01に4要素が存在し、パスワード欄が type=password', () => {
  const form = s01.render({}, app);
  assert.ok(form.querySelector('[name="user_id"]'));
  assert.ok(form.querySelector('[name="password"]'));
  assert.equal(form.querySelector('[name="password"]').getAttribute('type'), 'password');
  assert.ok(form.querySelector('[data-action="login"]'));
  assert.ok(form.querySelector('[data-top-message]'));
});

test('手順2: 空入力ではAPIを呼ばず、両フィールドに日本語のエラーが出る', async () => {
  let called = 0;
  api.runtime.fetch = async (...args) => { called += 1; return httpFetch(...args); };
  const form = s01.render({}, app);
  fill(form, '', '');
  await s01.submit(form);
  assert.equal(called, 0);
  assert.equal(form.querySelector('[data-error-for="user_id"]').textContent, 'ユーザーIDを入力してください。');
  assert.equal(form.querySelector('[data-error-for="password"]').textContent, 'パスワードを入力してください。');
});

test('手順3: ab / 正しいパスワード ではAPIを呼ばずフィールドエラー', async () => {
  let called = 0;
  api.runtime.fetch = async (...args) => { called += 1; return httpFetch(...args); };
  const form = s01.render({}, app);
  fill(form, 'ab', 'Passw0rd!23');
  await s01.submit(form);
  assert.equal(called, 0);
  assert.equal(
    form.querySelector('[data-error-for="user_id"]').textContent,
    'ユーザーIDは半角英数字4〜20文字で入力してください。'
  );
});

test('手順4: 誤パスワードではAPIが呼ばれ、エラー領域に所定の文言。画面はS01のまま', async () => {
  const form = s01.render({}, app);
  fill(form, 'user001', 'WrongPass123');
  const ok = await s01.submit(form);
  assert.equal(ok, false);
  assert.equal(
    form.querySelector('[data-top-message]').textContent,
    'ユーザーIDまたはパスワードが正しくありません。'
  );
  assert.equal(globalThis.location.hash, '');
});

test('手順5: 正しい資格情報で #/calendar へ遷移し、送信中はボタンが非活性', async () => {
  const form = s01.render({}, app);
  fill(form, 'user001', 'Passw0rd!23');
  const button = form.querySelector('[data-action="login"]');
  const running = s01.submit(form);
  assert.equal(button.disabled, true, '送信中はボタンが非活性');
  assert.equal(await running, true);
  assert.equal(button.disabled, false);
  assert.equal(globalThis.location.hash, '#/calendar');
  // 発行されたセッションCookieで GET /api/me が通る
  const me = await httpFetch('/api/me');
  assert.equal(me.status, 200);
  assert.equal((await me.json()).user.user_id, 'user001');
});
