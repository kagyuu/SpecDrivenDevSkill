// T015 — S02カレンダーと予約APIの接続(docs/P008-test-direction/T015-calendar-grid-api.md)
// 実サーバー(uvicorn)に対して実行する。
import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import { installDom } from '../helpers/dom-env.js';
import { startServer, makeFetch } from '../helpers/server.js';
import * as api from '../../src/lib/api.js';
import { addDays, startOfWeek, today } from '../../src/lib/datetime.js';

let server;
let httpFetch;
let s02;
let env;
let calls;
const rooms = {};
let reservationId;

const TOMORROW = addDays(today(), 1);
const YESTERDAY = addDays(today(), -1);

async function callJson(path, method, body) {
  const options = { method, headers: { 'Content-Type': 'application/json' } };
  if (body) options.body = JSON.stringify(body);
  return httpFetch(path, options);
}

before(async () => {
  server = await startServer();
  httpFetch = makeFetch(server.baseUrl);
  // 事前準備: 基準データセット(ユーザー・会議室)を実APIで投入する
  assert.equal((await callJson('/api/auth/login', 'POST', { user_id: 'admin001', password: 'Passw0rd!23' })).status, 200);
  for (const user of [
    { user_id: 'user001', name: '山田 太郎', role: 'general', password: 'Passw0rd!23' },
    { user_id: 'user002', name: '鈴木 花子', role: 'general', password: 'Passw0rd!23' },
  ]) {
    assert.equal((await callJson('/api/users', 'POST', user)).status, 201);
  }
  for (const room of [
    { name: '会議室A', capacity: 10, equipment: 'プロジェクタ' },
    { name: '会議室B', capacity: 4 },
    { name: '会議室C', capacity: 20, is_active: false },
  ]) {
    const res = await callJson('/api/rooms', 'POST', room);
    assert.equal(res.status, 201);
    rooms[room.name] = (await res.json()).room.room_id;
  }
  // user001 で「本日+1日」会議室A 10:00-11:00 の予約を1件作る
  assert.equal((await callJson('/api/auth/login', 'POST', { user_id: 'user001', password: 'Passw0rd!23' })).status, 200);
  const created = await callJson('/api/reservations', 'POST', {
    room_id: rooms['会議室A'], reserved_date: TOMORROW, start_time: '10:00', end_time: '11:00',
    title: '定例会議', attendee_user_ids: [], attendee_count: 8, note: '',
  });
  assert.equal(created.status, 201);
  reservationId = (await created.json()).reservation.reservation_id;

  env = installDom();
  calls = [];
  api.runtime.fetch = async (path, options) => {
    calls.push(path);
    return httpFetch(path, options);
  };
  api.runtime.navigate = (hash) => { globalThis.location.hash = hash; };
  s02 = await import('../../src/views/s02-calendar.js');
  s02.resetState();
});

after(() => { if (server) server.stop(); });

function cell(root, date, roomId, slot) {
  return root.querySelector(
    `[data-cell][data-date="${date}"][data-room-id="${roomId}"][data-slot="${slot}"]`
  );
}

function apiCalls(prefix) {
  return calls.filter((p) => p.startsWith(prefix));
}

test('手順1: GET /api/rooms と GET /api/reservations がそれぞれ1回ずつ呼ばれる', async () => {
  calls.length = 0;
  await s02.render({ date: TOMORROW }, env.app, env.header);
  assert.equal(apiCalls('/api/rooms').length, 1);
  assert.equal(apiCalls('/api/reservations').length, 1);
});

test('手順2: 有効な会議室2列のみが列に現れる(無効な会議室Cは出ない)', () => {
  const grid = env.app.querySelector(`[data-role="day-grid"][data-date="${TOMORROW}"]`);
  const headers = grid.querySelectorAll('thead th');
  assert.equal(headers.length, 3); // 「時間」+ 会議室2列
  const names = headers.slice(1).map((th) => th.textContent);
  assert.deepEqual(names, ['会議室A', '会議室B']);
  assert.equal(names.includes('会議室C'), false);
});

test('手順3: 10:00 / 10:30 に「山田 太郎 / 定例会議」、11:00 は空き', () => {
  const root = env.app.querySelector('[data-view="s02-calendar"]');
  assert.equal(cell(root, TOMORROW, rooms['会議室A'], '10:00').textContent, '山田 太郎 / 定例会議');
  assert.equal(cell(root, TOMORROW, rooms['会議室A'], '10:30').textContent, '山田 太郎 / 定例会議');
  assert.equal(cell(root, TOMORROW, rooms['会議室A'], '11:00').textContent, '+');
});

test('手順4: 予約済みセルに参加予定人数(8)が表示されていない', () => {
  const root = env.app.querySelector('[data-view="s02-calendar"]');
  assert.equal(cell(root, TOMORROW, rooms['会議室A'], '10:00').textContent.includes('8'), false);
});

test('手順5: 会議室フィルタで会議室Aだけにすると列が1つに減り、APIは再呼び出しされない', () => {
  const root = env.app.querySelector('[data-view="s02-calendar"]');
  calls.length = 0;
  const box = root.querySelector(`[data-role="room-filter"][data-room-id="${rooms['会議室A']}"]`);
  box.checked = true;
  box.dispatchEvent({ type: 'change', target: box });
  const grid = env.app.querySelector(`[data-role="day-grid"][data-date="${TOMORROW}"]`);
  assert.equal(grid.querySelectorAll('thead th').length, 2);
  assert.equal(calls.length, 0);
});

test('手順6: 「翌週」で date_from が7日進んだ状態でAPIが呼ばれる', async () => {
  const root = env.app.querySelector('[data-view="s02-calendar"]');
  const weekStart = startOfWeek(TOMORROW);
  calls.length = 0;
  await root.querySelector('[data-action="next-week"]').click();
  const reservationCall = apiCalls('/api/reservations')[0];
  assert.ok(reservationCall.includes(`date_from=${addDays(weekStart, 7)}`), reservationCall);
});

test('手順7: 空きセル(会議室B 14:00)のクリックでS03へ値を引き継ぐ', async () => {
  s02.resetState();
  const root = await s02.render({ date: TOMORROW }, env.app, env.header);
  globalThis.location.hash = '';
  cell(root, TOMORROW, rooms['会議室B'], '14:00').click();
  assert.equal(
    globalThis.location.hash,
    `#/reservations/new?room_id=${rooms['会議室B']}&date=${TOMORROW}&start=14:00&end=14:30`
  );
});

test('手順8: 予約済みセルのクリックで #/reservations/{id} へ', () => {
  const root = env.app.querySelector('[data-view="s02-calendar"]');
  globalThis.location.hash = '';
  cell(root, TOMORROW, rooms['会議室A'], '10:00').click();
  assert.equal(globalThis.location.hash, `#/reservations/${reservationId}`);
});

test('手順9: 過去日(本日-1日)の空きセルは遷移せずメッセージが出る', async () => {
  s02.resetState();
  const root = await s02.render({ date: YESTERDAY }, env.app, env.header);
  globalThis.location.hash = '';
  cell(root, YESTERDAY, rooms['会議室A'], '14:00').click();
  assert.equal(globalThis.location.hash, '');
  assert.equal(
    root.querySelector('[data-top-message]').textContent,
    '過去の日付には予約できません。'
  );
});
