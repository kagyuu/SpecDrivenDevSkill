// T018 — S05の期間フィルタ(docs/P008-test-direction/T018-my-reservations-filter.md)
// 実サーバー(uvicorn)に対して実行する。過去の予約は日付検証を回避するためリポジトリ経由で直接INSERTする。
import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { installDom } from '../helpers/dom-env.js';
import { startServer, makeFetch } from '../helpers/server.js';
import * as api from '../../src/lib/api.js';
import { addDays, today } from '../../src/lib/datetime.js';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const SERVER_DIR = path.resolve(HERE, '..', '..', '..', 'server');

let server;
let httpFetch;
let s05;
let env;
let calls;
const rooms = {};
const created = {};

const D1 = addDays(today(), 1);
const D2 = addDays(today(), 2);
const D3 = addDays(today(), 3);
const PAST = addDays(today(), -2);

async function callJson(pathname, method, body) {
  const options = { method, headers: { 'Content-Type': 'application/json' } };
  if (body) options.body = JSON.stringify(body);
  return httpFetch(pathname, options);
}

async function loginAs(userId) {
  const res = await callJson('/api/auth/login', 'POST', { user_id: userId, password: 'Passw0rd!23' });
  assert.equal(res.status, 200);
}

// 過去日の予約はAPIから登録できないため、Repository経由で直接INSERTする(T018 テストデータ)。
function insertPastReservation(dbPath, roomId, userId, reservedDate) {
  const script = [
    'from meeting_room import db, security',
    'from meeting_room.repositories import reservations_repo',
    'import sys',
    'conn = db.connect(sys.argv[1])',
    'with db.transaction(conn):',
    '    rid = reservations_repo.insert(conn, int(sys.argv[2]), sys.argv[3], sys.argv[4],',
    '                                   "10:00", "11:00", "過去会議", None, "", security.now_utc())',
    'print(rid)',
  ].join('\n');
  const out = execFileSync(
    'python3',
    ['-c', script, dbPath, String(roomId), userId, reservedDate],
    { cwd: SERVER_DIR, env: { ...process.env, PYTHONPATH: path.join(SERVER_DIR, 'src') } }
  );
  return Number(String(out).trim());
}

before(async () => {
  server = await startServer();
  httpFetch = makeFetch(server.baseUrl);
  await loginAs('admin001');
  for (const user of [
    { user_id: 'user001', name: '山田 太郎', role: 'general', password: 'Passw0rd!23' },
    { user_id: 'user002', name: '鈴木 花子', role: 'general', password: 'Passw0rd!23' },
    // ★FIXME★(T018 手順6): 基準データセットの user003 は無効ユーザーのため、
    // 予約を持たない**有効**ユーザーを別途1件用意する
    { user_id: 'user004', name: '予約なし 花子', role: 'general', password: 'Passw0rd!23' },
  ]) {
    assert.equal((await callJson('/api/users', 'POST', user)).status, 201);
  }
  for (const room of [{ name: '会議室A', capacity: 10 }, { name: '会議室B', capacity: 4 }]) {
    const res = await callJson('/api/rooms', 'POST', room);
    assert.equal(res.status, 201);
    rooms[room.name] = (await res.json()).room.room_id;
  }

  await loginAs('user001');
  for (const [key, date] of [['d1', D1], ['d3', D3]]) {
    const res = await callJson('/api/reservations', 'POST', {
      room_id: rooms['会議室A'], reserved_date: date, start_time: '10:00', end_time: '11:00',
      title: `予定${key}`, attendee_user_ids: [], attendee_count: null, note: '',
    });
    assert.equal(res.status, 201);
    created[key] = (await res.json()).reservation.reservation_id;
  }
  created.past = insertPastReservation(server.dbPath, rooms['会議室A'], 'user001', PAST);

  await loginAs('user002');
  const other = await callJson('/api/reservations', 'POST', {
    room_id: rooms['会議室B'], reserved_date: D2, start_time: '10:00', end_time: '11:00',
    title: '他人の予約', attendee_user_ids: [], attendee_count: null, note: '',
  });
  assert.equal(other.status, 201);

  env = installDom();
  calls = [];
  api.runtime.fetch = async (pathname, options) => {
    calls.push(pathname);
    return httpFetch(pathname, options);
  };
  api.runtime.navigate = (hash) => { globalThis.location.hash = hash; };
  s05 = await import('../../src/views/s05-my-reservations.js');
  await loginAs('user001');
});

after(() => { if (server) server.stop(); });

function mineCalls() {
  return calls.filter((p) => p.startsWith('/api/reservations/mine'));
}

let root;

test('手順1: 初期表示で period=upcoming が呼ばれる', async () => {
  calls.length = 0;
  root = await s05.render({}, env.app, env.header);
  assert.equal(mineCalls().length, 1);
  assert.ok(mineCalls()[0].includes('period=upcoming'), mineCalls()[0]);
});

test('手順2: 2行(日付昇順)・4列で、他人の予約は含まれない', () => {
  const rows = root.querySelectorAll('[data-role="reservation-rows"] tr');
  assert.equal(rows.length, 2);
  assert.deepEqual(
    rows.map((r) => r.querySelector('[data-column="reserved_date"]').textContent),
    [D1, D3]
  );
  assert.equal(rows[0].querySelectorAll('td').length, 4);
  assert.deepEqual(
    root.querySelectorAll('[data-role="reservation-list"] thead th').map((th) => th.textContent),
    ['日付', '会議室名', '時間帯', '件名']
  );
  const titles = rows.map((r) => r.querySelector('[data-column="title"]').textContent);
  assert.equal(titles.includes('他人の予約'), false);
});

test('手順3・4: 「過去の予約」に切り替えると period=past で1行になる', async () => {
  calls.length = 0;
  const past = root.querySelector('[data-role="period"][data-period="past"]');
  past.checked = true;
  await past.dispatchEvent({ type: 'change', target: past })[0];
  assert.equal(mineCalls().length, 1);
  assert.ok(mineCalls()[0].includes('period=past'), mineCalls()[0]);
  const rows = env.app.querySelectorAll('[data-role="reservation-rows"] tr');
  assert.equal(rows.length, 1);
  assert.equal(rows[0].querySelector('[data-column="reserved_date"]').textContent, PAST);
});

test('手順5: 行クリックで #/reservations/{id} へ遷移する', () => {
  const row = env.app.querySelectorAll('[data-role="reservation-rows"] tr')[0];
  globalThis.location.hash = '';
  row.click();
  assert.equal(globalThis.location.hash, `#/reservations/${created.past}`);
});

test('手順6: 予約を持たない有効ユーザーでは「該当する予約はありません。」が出る', async () => {
  await loginAs('user004');
  const empty = await s05.render({}, env.app, env.header);
  assert.equal(
    empty.querySelector('[data-role="empty-message"]').textContent,
    '該当する予約はありません。'
  );
  assert.equal(empty.querySelector('[data-role="reservation-list"]'), null);
});
