// U004-T1 単体テスト — S02 予約カレンダー画面(P002 3.2 / 2.3 / 2.4)
import { test, beforeEach } from 'node:test';
import assert from 'node:assert/strict';
import { installDom } from './helpers/dom-env.js';
import * as api from '../src/lib/api.js';
import { addDays, startOfWeek, today } from '../src/lib/datetime.js';

let s02;
let app;
let header;
let calls;
let reservations;
let unauthorized;

const ME = { user_id: 'user001', name: '山田 太郎', role: 'general' };
const ROOMS = [
  { room_id: 1, name: '会議室A', capacity: 10, is_active: true },
  { room_id: 2, name: '会議室B', capacity: 4, is_active: true },
];

const TOMORROW = addDays(today(), 1);
const YESTERDAY = addDays(today(), -1);

function reservation(overrides = {}) {
  return {
    reservation_id: 12,
    room_id: 1,
    room_name: '会議室A',
    user_id: 'user001',
    user_name: '山田 太郎',
    reserved_date: TOMORROW,
    start_time: '10:00',
    end_time: '11:00',
    title: '定例会議',
    attendee_count: 8,
    attendees: [],
    ...overrides,
  };
}

beforeEach(async () => {
  const env = installDom();
  app = env.app;
  header = env.header;
  calls = [];
  reservations = [];
  unauthorized = false;
  api.runtime.navigate = (hash) => { globalThis.location.hash = hash; };
  api.runtime.fetch = async (path, options) => {
    calls.push({ path, method: options.method });
    if (path === '/api/me') return { status: 200, json: async () => ({ user: ME }) };
    if (path.startsWith('/api/rooms')) return { status: 200, json: async () => ({ rooms: ROOMS }) };
    if (path.startsWith('/api/reservations')) {
      if (unauthorized) {
        return {
          status: 401,
          json: async () => ({ error: { code: 'UNAUTHENTICATED', message: 'セッション切れ' } }),
        };
      }
      return { status: 200, json: async () => ({ reservations }) };
    }
    return { status: 204, json: async () => null };
  };
  api.takePendingMessage();
  s02 = await import('../src/views/s02-calendar.js');
  s02.resetState();
});

function reservationCalls() {
  return calls.filter((c) => c.path.startsWith('/api/reservations'));
}

function cell(root, date, roomId, slot) {
  return root.querySelector(
    `[data-cell][data-date="${date}"][data-room-id="${roomId}"][data-slot="${slot}"]`
  );
}

test('描画: 週(月曜起点7日)のグリッドが描かれ、会議室が列になる', async () => {
  const root = await s02.render({}, app, header);
  const grids = root.querySelectorAll('[data-role="day-grid"]');
  assert.equal(grids.length, 7);
  assert.equal(grids[0].getAttribute('data-date'), startOfWeek(today()));
  // 「時間」列 + 会議室2列
  assert.equal(grids[0].querySelectorAll('thead th').length, 3);
  // ヘッダーが描画される(一般ユーザーなので2リンク)
  assert.equal(header.querySelectorAll('a').length, 2);
});

test('描画: /api/rooms と /api/reservations をそれぞれ1回だけ呼ぶ', async () => {
  await s02.render({}, app, header);
  assert.equal(calls.filter((c) => c.path.startsWith('/api/rooms')).length, 1);
  assert.equal(reservationCalls().length, 1);
});

test('占有: 10:00-11:00 の予約は 10:00 / 10:30 を占有し 11:00 は空き', async () => {
  reservations = [reservation()];
  const root = await s02.render({ date: TOMORROW }, app, header);
  assert.equal(cell(root, TOMORROW, 1, '10:00').textContent, '山田 太郎 / 定例会議');
  assert.equal(cell(root, TOMORROW, 1, '10:30').textContent, '山田 太郎 / 定例会議');
  assert.equal(cell(root, TOMORROW, 1, '11:00').textContent, '+');
});

test('占有: 参加予定人数はセルに表示しない', async () => {
  reservations = [reservation()];
  const root = await s02.render({ date: TOMORROW }, app, header);
  assert.equal(cell(root, TOMORROW, 1, '10:00').textContent.includes('8'), false);
});

test('配色: 自分の予約に is-mine が付き、他人の予約には付かない', async () => {
  reservations = [
    reservation(),
    reservation({ reservation_id: 13, room_id: 2, user_id: 'user002', user_name: '鈴木 花子' }),
  ];
  const root = await s02.render({ date: TOMORROW }, app, header);
  assert.ok(cell(root, TOMORROW, 1, '10:00').className.includes('is-mine'));
  assert.equal(cell(root, TOMORROW, 2, '10:00').className.includes('is-mine'), false);
});

test('予約0件なら全セルが空き表示', async () => {
  const root = await s02.render({ date: TOMORROW }, app, header);
  const cells = root.querySelectorAll('[data-cell]');
  assert.ok(cells.length > 0);
  assert.ok(cells.every((c) => c.textContent === '+'));
});

test('フィルタ: 会議室Aだけを選ぶと列が減り、APIは再取得されない', async () => {
  const root = await s02.render({ date: TOMORROW }, app, header);
  const before = reservationCalls().length;
  const box = root.querySelector('[data-role="room-filter"][data-room-id="1"]');
  box.checked = true;
  box.dispatchEvent({ type: 'change', target: box });
  const grids = app.querySelectorAll('[data-role="day-grid"]');
  assert.equal(grids[0].querySelectorAll('thead th').length, 2); // 時間 + 会議室A
  assert.equal(reservationCalls().length, before);
});

test('翌週: 表示週が+7日になり、date_from が7日進んで再取得される', async () => {
  const root = await s02.render({ date: TOMORROW }, app, header);
  const weekStart = startOfWeek(TOMORROW);
  await s02.changeDate(root, addDays(s02.getState().date, 7));
  const last = reservationCalls()[reservationCalls().length - 1];
  assert.ok(last.path.includes(`date_from=${addDays(weekStart, 7)}`), last.path);
  const grids = app.querySelectorAll('[data-role="day-grid"]');
  assert.equal(grids[0].getAttribute('data-date'), addDays(weekStart, 7));
});

test('遷移: 予約済みセルのクリックで #/reservations/{id} へ', async () => {
  reservations = [reservation()];
  const root = await s02.render({ date: TOMORROW }, app, header);
  cell(root, TOMORROW, 1, '10:00').click();
  assert.equal(globalThis.location.hash, '#/reservations/12');
});

test('遷移: 空きセルのクリックで S03 へ値を引き継ぐ(終了は開始+30分)', async () => {
  const root = await s02.render({ date: TOMORROW }, app, header);
  cell(root, TOMORROW, 2, '14:00').click();
  assert.equal(
    globalThis.location.hash,
    `#/reservations/new?room_id=2&date=${TOMORROW}&start=14:00&end=14:30`
  );
});

test('過去日の空きセルはS03へ遷移せずメッセージを表示する', async () => {
  const root = await s02.render({ date: YESTERDAY }, app, header);
  globalThis.location.hash = '';
  cell(root, YESTERDAY, 1, '14:00').click();
  assert.equal(globalThis.location.hash, '');
  assert.equal(root.querySelector('[data-top-message]').textContent, '過去の日付には予約できません。');
});

test('401: GET /api/reservations が401ならS01へ戻る導線が働く', async () => {
  unauthorized = true;
  await s02.render({ date: TOMORROW }, app, header);
  assert.equal(globalThis.location.hash, '#/login');
});

test('flash: setFlash した文言が次回のS02描画で画面上部に出る', async () => {
  s02.setFlash('予約を登録しました。');
  const root = await s02.render({ date: TOMORROW }, app, header);
  assert.equal(root.querySelector('[data-top-message]').textContent, '予約を登録しました。');
  // 1回限り
  const again = await s02.render({ date: TOMORROW }, app, header);
  assert.equal(again.querySelector('[data-top-message]').textContent, '');
});
