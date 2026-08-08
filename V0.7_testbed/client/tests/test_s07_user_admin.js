// U002-T5 単体テスト — S07 ユーザー管理画面(P002 3.7 / 2.3 / 2.4)
import { test, beforeEach } from 'node:test';
import assert from 'node:assert/strict';
import { installDom } from './helpers/dom-env.js';
import * as api from '../src/lib/api.js';

let s07;
let app;
let calls;
let responses;

const ADMIN = { user_id: 'admin001', name: '初期管理者', role: 'admin' };
const GENERAL = { user_id: 'user001', name: '山田 太郎', role: 'general' };
const USERS = [
  { user_id: 'admin001', name: '初期管理者', role: 'admin', is_active: true },
  { user_id: 'user001', name: '山田 太郎', role: 'general', is_active: true },
  { user_id: 'user002', name: '鈴木 花子', role: 'general', is_active: true },
  { user_id: 'user003', name: '無効 三郎', role: 'general', is_active: false },
];

beforeEach(async () => {
  app = installDom().app;
  calls = [];
  responses = {};
  api.runtime.navigate = (hash) => { globalThis.location.hash = hash; };
  api.runtime.fetch = async (path, options) => {
    calls.push({ path, method: options.method, body: options.body ? JSON.parse(options.body) : null });
    const canned = responses[`${options.method} ${path}`];
    if (canned) return canned;
    if (path.startsWith('/api/users')) return { status: 200, json: async () => ({ users: USERS }) };
    if (path === '/api/me') return { status: 200, json: async () => ({ user: ADMIN }) };
    return { status: 204, json: async () => null };
  };
  api.takePendingMessage();
  s07 = await import('../src/views/s07-user-admin.js');
});

function errorResponse(status, code, message) {
  return { status, json: async () => ({ error: { code, message } }) };
}

function fillForm(root, values) {
  const form = root.querySelector('[data-role="user-form"]');
  for (const [name, value] of Object.entries(values)) {
    const input = form.querySelector(`[name="${name}"]`);
    if (name === 'is_active') input.checked = value;
    else input.value = value;
  }
  return form;
}

test('一覧: 4件描画され、無効行に is-inactive が付き「戻る」リンクがある', () => {
  const root = s07.view(app, ADMIN, USERS);
  const rows = root.querySelectorAll('[data-role="user-rows"] tr');
  assert.equal(rows.length, 4);
  assert.equal(rows[3].className, 'is-inactive');
  assert.ok(root.querySelector('[data-link="back"]'));
});

test('新規登録: POST /api/users のボディに password が含まれる', async () => {
  const root = s07.view(app, ADMIN, USERS);
  root.querySelector('[data-action="new"]').click();
  fillForm(root, { user_id: 'user900', name: '新規 太郎', role: 'general', password: 'Passw0rd!23', is_active: true });
  assert.equal(await s07.submit(app), true);
  const post = calls.find((c) => c.method === 'POST');
  assert.equal(post.path, '/api/users');
  assert.deepEqual(post.body, {
    name: '新規 太郎', role: 'general', is_active: true, password: 'Passw0rd!23', user_id: 'user900',
  });
});

test('編集: パスワード空欄なら password キーを含めず、社員ID欄は非活性', async () => {
  const root = s07.view(app, ADMIN, USERS);
  root.querySelectorAll('[data-action="edit"]')[1].click();
  const form = root.querySelector('[data-role="user-form"]');
  assert.equal(form.querySelector('[name="user_id"]').disabled, true);
  assert.equal(form.querySelector('[name="user_id"]').value, 'user001');
  assert.match(form.querySelector('[data-role="password-label"]').textContent, /空欄なら変更しない/);
  form.querySelector('[name="name"]').value = '山田 次郎';
  assert.equal(await s07.submit(app), true);
  const put = calls.find((c) => c.method === 'PUT');
  assert.equal(put.path, '/api/users/user001');
  assert.equal('password' in put.body, false);
  assert.equal(put.body.name, '山田 次郎');
});

test('権限: 一般ユーザーには一覧を描画せず権限メッセージのみ', () => {
  const root = s07.view(app, GENERAL, USERS);
  assert.equal(root.querySelector('[data-role="user-list"]'), null);
  assert.equal(root.querySelector('[data-permission-message]').textContent, 'この画面を表示する権限がありません。');
});

test('パスワード7文字: APIを呼ばずエラー表示', async () => {
  const root = s07.view(app, ADMIN, USERS);
  root.querySelector('[data-action="new"]').click();
  fillForm(root, { user_id: 'user900', name: '新規 太郎', role: 'general', password: 'short12', is_active: true });
  assert.equal(await s07.submit(app), false);
  assert.equal(calls.length, 0);
  assert.equal(
    root.querySelector('[data-error-for="password"]').textContent,
    'パスワードは8〜64文字で入力してください。'
  );
});

test('409 DUPLICATE_KEY: 社員ID欄の直下にメッセージ', async () => {
  const root = s07.view(app, ADMIN, USERS);
  root.querySelector('[data-action="new"]').click();
  responses['POST /api/users'] = errorResponse(409, 'DUPLICATE_KEY', 'この社員IDはすでに登録されています。');
  fillForm(root, { user_id: 'user001', name: '新規 太郎', role: 'general', password: 'Passw0rd!23', is_active: true });
  assert.equal(await s07.submit(app), false);
  assert.equal(
    app.querySelector('[data-error-for="user_id"]').textContent,
    'この社員IDはすでに登録されています。'
  );
});

test('409 CONSTRAINT_VIOLATION: 画面上部にAPIの message', async () => {
  s07.view(app, ADMIN, USERS);
  responses['DELETE /api/users/admin001'] = errorResponse(
    409, 'CONSTRAINT_VIOLATION', '自分自身を無効化することはできません。'
  );
  globalThis.confirm = () => true;
  assert.equal(await s07.remove(app, 'admin001'), false);
  assert.equal(app.querySelector('[data-top-message]').textContent, '自分自身を無効化することはできません。');
});

test('削除: 確認キャンセルでは DELETE が呼ばれない', async () => {
  s07.view(app, ADMIN, USERS);
  globalThis.confirm = () => false;
  assert.equal(await s07.remove(app, 'user002'), false);
  assert.equal(calls.filter((c) => c.method === 'DELETE').length, 0);
});
