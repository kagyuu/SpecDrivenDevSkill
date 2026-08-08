// A005 — マイ予約とカレンダーの整合(docs/P009-acceptance-direction/A005-my-reservations-consistency.md)
import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { installDom } from '../helpers/dom-env.js';
import { startWithBaseData, PASSWORD } from './support.js';
import * as api from '../../src/lib/api.js';
import { addDays, startOfWeek, today } from '../../src/lib/datetime.js';

let server;
let httpFetch;
let roomIds;
let env;
let s02;
let s04;
let s05;

const D1 = addDays(today(), 1); // user001
const D2 = addDays(today(), 2); // user002
const D3 = addDays(today(), 3); // user001
const PAST = addDays(today(), -2); // user001 の過去予約(直接INSERT)
const created = {};

// 過去日の予約はAPIから作れない(400)ため、DBへ直接INSERTする(A005 の指示どおり)。
function insertPastReservation(dbPath, roomId) {
  const script = `
import sqlite3, sys
conn = sqlite3.connect(sys.argv[1])
cur = conn.execute(
    "INSERT INTO reservations(room_id, user_id, reserved_date, start_time, end_time,"
    " title, attendee_count, note, created_at, updated_at)"
    " VALUES (?, 'user001', ?, '09:00', '10:00', '過去の打合せ', NULL, '',"
    " '2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z')",
    (int(sys.argv[2]), sys.argv[3]),
)
conn.commit()
print(cur.lastrowid)
`;
  const out = execFileSync('python3', ['-c', script, dbPath, String(roomId), PAST], {
    encoding: 'utf8',
  });
  return Number(out.trim());
}

before(async () => {
  let callJson;
  ({ server, httpFetch, callJson, roomIds } = await startWithBaseData());

  async function makeReservation(userId, date, start, end, title) {
    assert.equal(
      (await callJson('/api/auth/login', 'POST', { user_id: userId, password: PASSWORD })).status,
      200
    );
    const res = await callJson('/api/reservations', 'POST', {
      room_id: roomIds['会議室A'], reserved_date: date, start_time: start, end_time: end,
      title, attendee_user_ids: [], attendee_count: null, note: '',
    });
    const payload = await res.json();
    assert.equal(res.status, 201, JSON.stringify(payload));
    return payload.reservation.reservation_id;
  }

  created.d1 = await makeReservation('user001', D1, '10:00', '11:00', '自分の予約1');
  created.d3 = await makeReservation('user001', D3, '14:00', '15:00', '自分の予約2');
  created.d2 = await makeReservation('user002', D2, '10:00', '11:00', '他人の予約');
  created.past = insertPastReservation(server.dbPath, roomIds['会議室A']);

  // 事前準備2: user001 でログインする
  assert.equal(
    (await callJson('/api/auth/login', 'POST', { user_id: 'user001', password: PASSWORD })).status,
    200
  );

  env = installDom();
  api.runtime.fetch = httpFetch;
  api.runtime.navigate = (hash) => { globalThis.location.hash = hash; };
  s02 = await import('../../src/views/s02-calendar.js');
  s04 = await import('../../src/views/s04-reservation-detail.js');
  s05 = await import('../../src/views/s05-my-reservations.js');
  s02.resetState();
  s02.takeFlash();
});

after(() => { if (server) server.stop(); });

function grid() {
  return env.app.querySelector('[data-view="s02-calendar"]');
}

function cell(date, slot) {
  return grid().querySelector(
    `[data-cell][data-date="${date}"][data-room-id="${roomIds['会議室A']}"][data-slot="${slot}"]`
  );
}

// 対象日が現在表示している週の外なら、その週へ移動する。
async function showWeekOf(date) {
  const container = grid();
  if (!container || !container.querySelector(`[data-role="day-grid"][data-date="${date}"]`)) {
    await s02.changeDate(env.app, date);
  }
}

test('手順1: S02のグリッドに user001 の2件と user002 の1件がすべて表示される', async () => {
  await s02.render({ date: today() }, env.app, env.header);
  const week = startOfWeek(today());
  assert.equal(startOfWeek(today()), week);
  for (const [date, slot, label] of [
    [D1, '10:00', '山田 太郎 / 自分の予約1'],
    [D2, '10:00', '鈴木 花子 / 他人の予約'],
    [D3, '14:00', '山田 太郎 / 自分の予約2'],
  ]) {
    await showWeekOf(date);
    const target = cell(date, slot);
    assert.ok(target, `${date} ${slot} のセルがある`);
    assert.equal(target.textContent, label, `${date} ${slot}`);
  }
});

test('手順2: 自分の予約に is-mine が付き、他人の予約には付かない', async () => {
  await showWeekOf(D1);
  assert.ok(cell(D1, '10:00').className.includes('is-mine'), cell(D1, '10:00').className);
  await showWeekOf(D2);
  const others = cell(D2, '10:00');
  assert.ok(others.className.includes('is-reserved'), others.className);
  assert.ok(!others.className.includes('is-mine'), others.className);
});

test('手順3: S05(今後の予約)は自分の未来分2件のみ・日付昇順', async () => {
  const root = await s05.render({}, env.app, env.header);
  const rows = root.querySelectorAll('[data-role="reservation-rows"] tr');
  assert.equal(rows.length, 2, `件数: ${rows.length}`);
  const dates = rows.map((r) => r.querySelector('[data-column="reserved_date"]').textContent);
  assert.deepEqual(dates, [D1, D3], '日付昇順で自分の未来2件');
  const ids = rows.map((r) => r.getAttribute('data-reservation-id'));
  assert.ok(!ids.includes(String(created.d2)), '他人の予約を含まない');
  assert.ok(!ids.includes(String(created.past)), '過去予約を含まない');
});

test('手順4: S05の1行目からS04へ遷移し、S02のセルと内容が一致する', async () => {
  const root = env.app.querySelector('[data-view="s05-my-reservations"]');
  const first = root.querySelector('[data-role="reservation-rows"] tr');
  first.click();
  assert.equal(globalThis.location.hash, `#/reservations/${created.d1}`);
  const detail = await s04.render({ reservation_id: String(created.d1) }, env.app, env.header);
  const value = (field) => detail.querySelector(`[data-field="${field}"]`).textContent;
  assert.equal(value('room_name'), '会議室A');
  assert.equal(value('reserved_date'), D1);
  assert.equal(value('time_range'), '10:00-11:00');
  assert.equal(value('title'), '自分の予約1');
});

test('手順5: S05を「過去の予約」に切り替えると過去予約1件が表示される', async () => {
  const root = await s05.render({}, env.app, env.header);
  const radio = root.querySelector('[data-role="period"][data-period="past"]');
  radio.checked = true;
  await s05.changePeriod(root, 'past');
  const list = env.app.querySelector('[data-view="s05-my-reservations"]');
  const rows = list.querySelectorAll('[data-role="reservation-rows"] tr');
  assert.equal(rows.length, 1, `過去の件数: ${rows.length}`);
  assert.equal(rows[0].querySelector('[data-column="reserved_date"]').textContent, PAST);
  assert.equal(rows[0].querySelector('[data-column="title"]').textContent, '過去の打合せ');
});

test('手順6: S04で1件取消すると、S02とS05の両方から消える', async () => {
  const detail = await s04.render({ reservation_id: String(created.d1) }, env.app, env.header);
  globalThis.confirm = () => true;
  assert.equal(await s04.remove(detail), true);

  s02.resetState();
  await s02.render({ date: today() }, env.app, env.header);
  await showWeekOf(D1);
  assert.equal(cell(D1, '10:00').textContent, '+', 'S02のグリッドから消える');

  const list = await s05.render({}, env.app, env.header);
  const rows = list.querySelectorAll('[data-role="reservation-rows"] tr');
  assert.equal(rows.length, 1, `S05の残り件数: ${rows.length}`);
  assert.equal(rows[0].getAttribute('data-reservation-id'), String(created.d3));
});
