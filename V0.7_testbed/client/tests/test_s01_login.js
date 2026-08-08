// U001-T6 単体テスト — S01 ログイン画面(P002 3.1 / 2.4)
import { test, beforeEach } from 'node:test';
import assert from 'node:assert/strict';
import { installDom } from './helpers/dom-env.js';
import * as api from '../src/lib/api.js';

let s01;
let app;
let calls;

beforeEach(async () => {
  const env = installDom();
  app = env.app;
  calls = [];
  api.runtime.navigate = (hash) => { globalThis.location.hash = hash; };
  api.runtime.fetch = async () => { throw new Error('fetch が設定されていません'); };
  api.takePendingMessage();
  s01 = await import('../src/views/s01-login.js');
});

function stubApi(status, payload) {
  api.runtime.fetch = async (path, options) => {
    calls.push({ path, options });
    return { status, json: async () => payload };
  };
}

function fill(form, userId, password) {
  form.querySelector('[name="user_id"]').value = userId;
  form.querySelector('[name="password"]').value = password;
}

test('描画: 入力欄・ボタン・エラー領域が揃う', () => {
  const form = s01.render({}, app);
  assert.ok(form.querySelector('[name="user_id"]'));
  assert.equal(form.querySelector('[name="password"]').getAttribute('type'), 'password');
  assert.ok(form.querySelector('[data-action="login"]'));
  assert.ok(form.querySelector('[data-top-message]'));
  // S01では共通ヘッダーを描画しない
  assert.equal(globalThis.document.getElementById('header').childNodes.length, 0);
});

test('空入力: APIを呼ばず両フィールドにエラーが出る', async () => {
  const form = s01.render({}, app);
  fill(form, '', '');
  await s01.submit(form);
  assert.equal(calls.length, 0);
  assert.equal(form.querySelector('[data-error-for="user_id"]').textContent, 'ユーザーIDを入力してください。');
  assert.equal(form.querySelector('[data-error-for="password"]').textContent, 'パスワードを入力してください。');
});

test('形式違反: APIを呼ばずユーザーID欄にエラーが出る', async () => {
  const form = s01.render({}, app);
  fill(form, 'ab', 'Passw0rd!23');
  await s01.submit(form);
  assert.equal(calls.length, 0);
  assert.equal(
    form.querySelector('[data-error-for="user_id"]').textContent,
    'ユーザーIDは半角英数字4〜20文字で入力してください。'
  );
});

test('成功: APIが1回呼ばれ #/calendar へ遷移する', async () => {
  stubApi(200, { user: { user_id: 'user001', name: '山田 太郎', role: 'general' } });
  const form = s01.render({}, app);
  fill(form, 'user001', 'Passw0rd!23');
  const ok = await s01.submit(form);
  assert.equal(ok, true);
  assert.equal(calls.length, 1);
  assert.equal(calls[0].path, '/api/auth/login');
  assert.deepEqual(JSON.parse(calls[0].options.body), { user_id: 'user001', password: 'Passw0rd!23' });
  assert.equal(globalThis.location.hash, '#/calendar');
});

test('401: エラー領域に所定の文言を表示し、画面はS01のまま', async () => {
  stubApi(401, { error: { code: 'AUTH_FAILED', message: 'ユーザーIDまたはパスワードが正しくありません。' } });
  const form = s01.render({}, app);
  fill(form, 'user001', 'WrongPass123');
  await s01.submit(form);
  assert.equal(form.querySelector('[data-top-message]').textContent, 'ユーザーIDまたはパスワードが正しくありません。');
  assert.equal(globalThis.location.hash, '');
});

test('送信中: ログインボタンが非活性になる', async () => {
  let release;
  const gate = new Promise((resolve) => { release = resolve; });
  api.runtime.fetch = async () => {
    await gate;
    return { status: 200, json: async () => ({ user: {} }) };
  };
  const form = s01.render({}, app);
  fill(form, 'user001', 'Passw0rd!23');
  const button = form.querySelector('[data-action="login"]');
  const running = s01.submit(form);
  assert.equal(button.disabled, true);
  release();
  await running;
  assert.equal(button.disabled, false);
});

test('セッション切れメッセージ: 描画時に1回だけ表示される', async () => {
  api.runtime.fetch = async () => ({ status: 401, json: async () => ({ error: { code: 'UNAUTHENTICATED', message: api.SESSION_EXPIRED_MESSAGE } }) });
  await assert.rejects(() => api.get('/api/me'));
  const form = s01.render({}, app);
  assert.equal(form.querySelector('[data-top-message]').textContent, api.SESSION_EXPIRED_MESSAGE);
  const again = s01.render({}, app);
  assert.equal(again.querySelector('[data-top-message]').textContent, '');
});

test('submit イベントからも送信できる', async () => {
  stubApi(200, { user: { user_id: 'user001', name: '山田 太郎', role: 'general' } });
  const form = s01.render({}, app);
  fill(form, 'user001', 'Passw0rd!23');
  await form.submit();
  assert.equal(calls.length, 1);
});
