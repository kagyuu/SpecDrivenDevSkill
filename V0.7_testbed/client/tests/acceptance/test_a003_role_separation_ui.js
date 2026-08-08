// A003 — 権限分離の横断確認(画面側 手順1・2)
// docs/P009-acceptance-direction/A003-role-separation.md
// API側は server/tests/acceptance/test_a003_role_separation.py が確認する。
import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import { installDom } from '../helpers/dom-env.js';
import { startWithBaseData, PASSWORD } from './support.js';
import * as api from '../../src/lib/api.js';
import { addDays, today } from '../../src/lib/datetime.js';

let server;
let httpFetch;
let roomIds;
let env;
let s06;
let s07;
let calls;

before(async () => {
  let callJson;
  ({ server, httpFetch, callJson, roomIds } = await startWithBaseData());
  // 事前準備1: user002 の予約1件
  assert.equal(
    (await callJson('/api/auth/login', 'POST', { user_id: 'user002', password: PASSWORD })).status,
    200
  );
  const res = await callJson('/api/reservations', 'POST', {
    room_id: roomIds['会議室A'], reserved_date: addDays(today(), 1),
    start_time: '09:00', end_time: '10:00', title: '他人の予約',
    attendee_user_ids: [], attendee_count: null, note: '',
  });
  assert.equal(res.status, 201, await res.text());
  // 事前準備2: user001 でログインする
  assert.equal(
    (await callJson('/api/auth/login', 'POST', { user_id: 'user001', password: PASSWORD })).status,
    200
  );

  env = installDom();
  calls = [];
  api.runtime.fetch = async (path, options) => {
    calls.push(`${options.method} ${path}`);
    return httpFetch(path, options);
  };
  api.runtime.navigate = (hash) => { globalThis.location.hash = hash; };
  s06 = await import('../../src/views/s06-room-admin.js');
  s07 = await import('../../src/views/s07-user-admin.js');
});

after(() => { if (server) server.stop(); });

test('手順1: 共通ヘッダーに「会議室管理」「ユーザー管理」リンクが描画されない', async () => {
  const s02 = await import('../../src/views/s02-calendar.js');
  s02.resetState();
  await s02.render({ date: today() }, env.app, env.header);
  const texts = env.header.querySelectorAll('a').map((a) => a.textContent);
  assert.ok(!texts.includes('会議室管理'), texts.join(','));
  assert.ok(!texts.includes('ユーザー管理'), texts.join(','));
  assert.equal(env.header.querySelector('[href="#/admin/rooms"]'), null);
  assert.equal(env.header.querySelector('[href="#/admin/users"]'), null);
  // 一般ユーザーにも出るリンクは残っている
  assert.ok(env.header.querySelector('[href="#/calendar"]'));
  assert.ok(env.header.querySelector('[href="#/my-reservations"]'));
});

test('手順2: #/admin/rooms を直接開くと権限メッセージのみで一覧データを取得しない', async () => {
  calls.length = 0;
  const root = await s06.render({}, env.app, env.header);
  assert.equal(
    root.querySelector('[data-permission-message]').textContent,
    'この画面を表示する権限がありません。'
  );
  assert.equal(root.querySelector('[data-role="room-list"]'), null, '会議室一覧テーブルを描かない');
  assert.deepEqual(
    calls.filter((c) => c.includes('/api/rooms')),
    [],
    `会議室一覧を取得していないこと: ${calls.join(' / ')}`
  );
});

test('手順2: #/admin/users を直接開くと権限メッセージのみで一覧データを取得しない', async () => {
  calls.length = 0;
  const root = await s07.render({}, env.app, env.header);
  assert.equal(
    root.querySelector('[data-permission-message]').textContent,
    'この画面を表示する権限がありません。'
  );
  assert.equal(root.querySelector('[data-role="user-list"]'), null, 'ユーザー一覧テーブルを描かない');
  assert.deepEqual(
    calls.filter((c) => c.includes('/api/users')),
    [],
    `ユーザー一覧を取得していないこと: ${calls.join(' / ')}`
  );
});
