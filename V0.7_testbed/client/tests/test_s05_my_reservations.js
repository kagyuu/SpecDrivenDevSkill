// U004-T4 単体テスト — S05 マイ予約一覧画面(P002 3.5 / 2.3)
import { test, beforeEach } from 'node:test';
import assert from 'node:assert/strict';
import { installDom } from './helpers/dom-env.js';
import * as api from '../src/lib/api.js';
import { addDays, today } from '../src/lib/datetime.js';

let s05;
let app;
let header;
let calls;
let byPeriod;
let unauthorized;

const ME = { user_id: 'user001', name: '山田 太郎', role: 'general' };

function reservation(overrides = {}) {
  return {
    reservation_id: 1,
    room_id: 1,
    room_name: '会議室A',
    user_id: 'user001',
    user_name: '山田 太郎',
    reserved_date: addDays(today(), 1),
    start_time: '10:00',
    end_time: '11:00',
    title: '定例会議',
    attendees: [],
    ...overrides,
  };
}

const UPCOMING = [
  reservation({ reservation_id: 1, reserved_date: addDays(today(), 1) }),
  reservation({ reservation_id: 2, reserved_date: addDays(today(), 3), title: '打合せ' }),
  reservation({ reservation_id: 3, reserved_date: addDays(today(), 5), title: '面談' }),
];
const PAST = [reservation({ reservation_id: 4, reserved_date: addDays(today(), -2), title: '過去会議' })];

beforeEach(async () => {
  const env = installDom();
  app = env.app;
  header = env.header;
  calls = [];
  byPeriod = { upcoming: UPCOMING, past: PAST };
  unauthorized = false;
  api.runtime.navigate = (hash) => { globalThis.location.hash = hash; };
  api.runtime.fetch = async (path, options) => {
    calls.push({ path, method: options.method });
    if (path === '/api/me') return { status: 200, json: async () => ({ user: ME }) };
    if (path.startsWith('/api/reservations/mine')) {
      if (unauthorized) {
        return {
          status: 401,
          json: async () => ({ error: { code: 'UNAUTHENTICATED', message: 'セッション切れ' } }),
        };
      }
      const period = path.includes('period=past') ? 'past' : 'upcoming';
      return { status: 200, json: async () => ({ reservations: byPeriod[period] }) };
    }
    return { status: 204, json: async () => null };
  };
  api.takePendingMessage();
  s05 = await import('../src/views/s05-my-reservations.js');
});

function mineCalls() {
  return calls.filter((c) => c.path.startsWith('/api/reservations/mine'));
}

test('初期表示: period=upcoming で呼ばれ、3行・4列で描画される', async () => {
  const root = await s05.render({}, app, header);
  assert.equal(mineCalls().length, 1);
  assert.ok(mineCalls()[0].path.includes('period=upcoming'));
  const rows = root.querySelectorAll('[data-role="reservation-rows"] tr');
  assert.equal(rows.length, 3);
  assert.equal(rows[0].querySelectorAll('td').length, 4);
  assert.deepEqual(
    root.querySelectorAll('[data-role="reservation-list"] thead th').map((th) => th.textContent),
    ['日付', '会議室名', '時間帯', '件名']
  );
});

test('並び順: APIの返却順をそのまま使う(再ソートしない)', async () => {
  const root = await s05.render({}, app, header);
  const rows = root.querySelectorAll('[data-role="reservation-rows"] tr');
  assert.deepEqual(
    rows.map((r) => r.querySelector('[data-column="reserved_date"]').textContent),
    UPCOMING.map((r) => r.reserved_date)
  );
});

test('列の内容: 日付 / 会議室名 / 時間帯 / 件名', async () => {
  const root = await s05.render({}, app, header);
  const first = root.querySelectorAll('[data-role="reservation-rows"] tr')[0];
  assert.equal(first.querySelector('[data-column="room_name"]').textContent, '会議室A');
  assert.equal(first.querySelector('[data-column="time_range"]').textContent, '10:00-11:00');
  assert.equal(first.querySelector('[data-column="title"]').textContent, '定例会議');
});

test('フィルタ: 「過去の予約」に切り替えると period=past で再取得される', async () => {
  const root = await s05.render({}, app, header);
  const past = root.querySelector('[data-role="period"][data-period="past"]');
  past.checked = true;
  await past.dispatchEvent({ type: 'change', target: past })[0];
  assert.equal(mineCalls().length, 2);
  assert.ok(mineCalls()[1].path.includes('period=past'));
  const rows = app.querySelectorAll('[data-role="reservation-rows"] tr');
  assert.equal(rows.length, 1);
  assert.equal(rows[0].querySelector('[data-column="title"]').textContent, '過去会議');
});

test('行クリックで #/reservations/{id} へ遷移する', async () => {
  const root = await s05.render({}, app, header);
  root.querySelectorAll('[data-role="reservation-rows"] tr')[1].click();
  assert.equal(globalThis.location.hash, '#/reservations/2');
});

test('0件のとき「該当する予約はありません。」が出る', async () => {
  byPeriod.upcoming = [];
  const root = await s05.render({}, app, header);
  assert.equal(root.querySelector('[data-role="empty-message"]').textContent, '該当する予約はありません。');
  assert.equal(root.querySelector('[data-role="reservation-list"]'), null);
});

test('401でS01へ戻る導線が働く', async () => {
  unauthorized = true;
  await assert.rejects(() => s05.render({}, app, header));
  assert.equal(globalThis.location.hash, '#/login');
});
