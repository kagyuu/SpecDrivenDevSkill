// T016 — S02→S03の値の引き継ぎと登録完了(docs/P008-test-direction/T016-create-flow.md)
// 実サーバー(uvicorn)に対して実行する。
import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import { installDom } from '../helpers/dom-env.js';
import { startServer, makeFetch } from '../helpers/server.js';
import * as api from '../../src/lib/api.js';
import { addDays, today } from '../../src/lib/datetime.js';

let server;
let httpFetch;
let s02;
let s03;
let env;
let calls;
const rooms = {};

const TOMORROW = addDays(today(), 1);

async function callJson(path, method, body) {
  const options = { method, headers: { 'Content-Type': 'application/json' } };
  if (body) options.body = JSON.stringify(body);
  return httpFetch(path, options);
}

before(async () => {
  server = await startServer();
  httpFetch = makeFetch(server.baseUrl);
  assert.equal((await callJson('/api/auth/login', 'POST', { user_id: 'admin001', password: 'Passw0rd!23' })).status, 200);
  for (const user of [
    { user_id: 'user001', name: '山田 太郎', role: 'general', password: 'Passw0rd!23' },
    { user_id: 'user002', name: '鈴木 花子', role: 'general', password: 'Passw0rd!23' },
  ]) {
    assert.equal((await callJson('/api/users', 'POST', user)).status, 201);
  }
  for (const room of [{ name: '会議室A', capacity: 10 }, { name: '会議室B', capacity: 4 }]) {
    const res = await callJson('/api/rooms', 'POST', room);
    assert.equal(res.status, 201);
    rooms[room.name] = (await res.json()).room.room_id;
  }
  // 既存予約: 「本日+1日」会議室A 10:00-11:00
  assert.equal((await callJson('/api/auth/login', 'POST', { user_id: 'user001', password: 'Passw0rd!23' })).status, 200);
  assert.equal(
    (await callJson('/api/reservations', 'POST', {
      room_id: rooms['会議室A'], reserved_date: TOMORROW, start_time: '10:00', end_time: '11:00',
      title: '既存予約', attendee_user_ids: [], attendee_count: null, note: '',
    })).status,
    201
  );

  env = installDom();
  calls = [];
  api.runtime.fetch = async (path, options) => {
    calls.push({ path, method: options.method });
    return httpFetch(path, options);
  };
  api.runtime.navigate = (hash) => { globalThis.location.hash = hash; };
  s02 = await import('../../src/views/s02-calendar.js');
  s03 = await import('../../src/views/s03-reservation-new.js');
  s02.resetState();
  s02.takeFlash();
});

after(() => { if (server) server.stop(); });

let s03Root;

function form() {
  return s03Root.querySelector('[data-role="reservation-form"]');
}

function field(role) {
  return form().querySelector(`[data-role="${role}"]`);
}

function postCalls() {
  return calls.filter((c) => c.path === '/api/reservations' && c.method === 'POST');
}

test('手順1: S02の空きセル(会議室A 14:00)クリックからS03へ初期値が引き継がれる', async () => {
  const calendar = await s02.render({ date: TOMORROW }, env.app, env.header);
  const cell = calendar.querySelector(
    `[data-cell][data-date="${TOMORROW}"][data-room-id="${rooms['会議室A']}"][data-slot="14:00"]`
  );
  cell.click();
  assert.equal(
    globalThis.location.hash,
    `#/reservations/new?room_id=${rooms['会議室A']}&date=${TOMORROW}&start=14:00&end=14:30`
  );
  s03Root = await s03.render(
    { room_id: String(rooms['会議室A']), date: TOMORROW, start: '14:00', end: '14:30' },
    env.app, env.header
  );
  assert.equal(field('room_id').value, String(rooms['会議室A']));
  assert.equal(field('reserved_date').value, TOMORROW);
  assert.equal(field('start_time').value, '14:00');
  assert.equal(field('end_time').value, '14:30');
});

test('手順2: 終日チェックONで 09:00 / 18:00 が自動入力される', () => {
  const allDay = field('all_day');
  allDay.checked = true;
  allDay.dispatchEvent({ type: 'change', target: allDay });
  assert.equal(field('start_time').value, '09:00');
  assert.equal(field('end_time').value, '18:00');
});

test('手順3: 開始を手動で 10:00 にしても保持され、チェックは外れない', () => {
  field('start_time').value = '10:00';
  assert.equal(field('start_time').value, '10:00');
  assert.equal(field('all_day').checked, true);
});

test('手順4: 件名未入力の登録はAPIを呼ばず、件名欄の直下にエラーが出る', async () => {
  const before = postCalls().length;
  assert.equal(await s03.submit(s03Root), false);
  assert.equal(postCalls().length, before);
  assert.equal(
    form().querySelector('[data-error-for="title"]').textContent,
    '件名を入力してください。'
  );
});

test('手順5: 参加者候補が一般ユーザーでも取得され描画されている', () => {
  assert.ok(calls.some((c) => c.path === '/api/users?scope=attendee_candidates'));
  const values = form().querySelectorAll('[data-role="attendee_user_ids"] option').map((o) => o.value);
  assert.ok(values.includes('user001'), values.join(','));
  assert.ok(values.includes('user002'), values.join(','));
});

test('手順6: 10:00-18:00 の登録は 409 になり、重複エラー領域に競合時間帯が出る(画面はS03のまま)', async () => {
  field('title').value = '打合せ';
  globalThis.location.hash = '';
  assert.equal(await s03.submit(s03Root), false);
  const text = form().querySelector('[data-role="conflict-error"]').textContent;
  assert.ok(text.includes('選択した時間帯はすでに予約されています。'), text);
  assert.ok(text.includes('10:00-11:00'), text);
  assert.equal(globalThis.location.hash, '');
});

test('手順7: 14:00-15:00 / 参加予定人数11 はクライアント側検証で止まり、欄の直下に出る', async () => {
  field('start_time').value = '14:00';
  field('end_time').value = '15:00';
  field('attendee_count').value = '11';
  const before = postCalls().length;
  globalThis.location.hash = '';
  assert.equal(await s03.submit(s03Root), false);
  // 期待結果(F001で修正): POST は呼ばれず、参加予定人数欄の直下にメッセージが出る。
  // 根拠: P002 3.3「送信時にクライアント側で検証する」/ 2.4「違反ではAPIを呼ばない」。
  // サーバー側の 400 CAPACITY_EXCEEDED は T013 手順1 が確認する。
  assert.equal(postCalls().length, before, 'POST /api/reservations が呼ばれないこと');
  assert.equal(
    form().querySelector('[data-error-for="attendee_count"]').textContent,
    '参加予定人数が会議室の収容人数(10名)を超えています。'
  );
  assert.equal(form().querySelector('[data-role="capacity-error"]').textContent, '');
  assert.equal(globalThis.location.hash, '', '画面はS03のまま');
});

test('手順8: 参加予定人数5で登録すると 201 → #/calendar に戻り、グリッドに新しい予約が出る', async () => {
  field('attendee_count').value = '5';
  assert.equal(await s03.submit(s03Root), true);
  assert.equal(globalThis.location.hash, '#/calendar');
  s02.resetState();
  const calendar = await s02.render({ date: TOMORROW }, env.app, env.header);
  assert.equal(calendar.querySelector('[data-top-message]').textContent, '予約を登録しました。');
  const cell = calendar.querySelector(
    `[data-cell][data-date="${TOMORROW}"][data-room-id="${rooms['会議室A']}"][data-slot="14:00"]`
  );
  assert.equal(cell.textContent, '山田 太郎 / 打合せ');
});

// ※CR-001 手順9・手順10(オンライン会議URL)
test('手順9: 不正なオンライン会議URLはクライアント側検証で止まり、欄の直下に出る', async () => {
  s03Root = await s03.render(
    { room_id: String(rooms['会議室A']), date: TOMORROW, start: '16:00', end: '16:30' },
    env.app, env.header
  );
  field('title').value = 'オンライン打合せ';
  field('meeting_url').value = 'example.com/meet';
  const before = postCalls().length;
  globalThis.location.hash = '';
  assert.equal(await s03.submit(s03Root), false);
  assert.equal(postCalls().length, before, 'POST /api/reservations が呼ばれないこと');
  assert.equal(
    form().querySelector('[data-error-for="meeting_url"]').textContent,
    'オンライン会議URLは http:// または https:// で始まるURLを入力してください。'
  );
  assert.equal(globalThis.location.hash, '', '画面はS03のまま');
});

test('手順10: 正しいオンライン会議URLに直すと 201 になり、S04で登録値が確認できる', async () => {
  field('meeting_url').value = 'https://example.com/meet/t016';
  assert.equal(await s03.submit(s03Root), true);
  assert.equal(globalThis.location.hash, '#/calendar');
  const res = await httpFetch(
    `/api/reservations?date_from=${TOMORROW}&date_to=${TOMORROW}`,
    { method: 'GET' }
  );
  const created = (await res.json()).reservations.find((r) => r.start_time === '16:00');
  assert.ok(created, '16:00 の予約が登録されている');
  assert.equal(created.meeting_url, 'https://example.com/meet/t016');
});
