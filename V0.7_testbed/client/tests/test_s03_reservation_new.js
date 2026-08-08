// U004-T2 単体テスト — S03 予約作成画面(P002 3.3 / 2.4 / 4)
import { test, beforeEach } from 'node:test';
import assert from 'node:assert/strict';
import { installDom } from './helpers/dom-env.js';
import * as api from '../src/lib/api.js';
import { addDays, today } from '../src/lib/datetime.js';

let s03;
let s02;
let app;
let header;
let calls;
let responses;

const ME = { user_id: 'user001', name: '山田 太郎', role: 'general' };
const ROOMS = [
  { room_id: 1, name: '会議室A', capacity: 10, is_active: true },
  { room_id: 2, name: '会議室B', capacity: 4, is_active: true },
];
const CANDIDATES = [
  { user_id: 'user001', name: '山田 太郎' },
  { user_id: 'user002', name: '鈴木 花子' },
];
const TOMORROW = addDays(today(), 1);

beforeEach(async () => {
  const env = installDom();
  app = env.app;
  header = env.header;
  calls = [];
  responses = {};
  api.runtime.navigate = (hash) => { globalThis.location.hash = hash; };
  api.runtime.fetch = async (path, options) => {
    calls.push({ path, method: options.method, body: options.body ? JSON.parse(options.body) : null });
    const canned = responses[`${options.method} ${path}`];
    if (canned) return canned;
    if (path === '/api/me') return { status: 200, json: async () => ({ user: ME }) };
    if (path.startsWith('/api/rooms')) return { status: 200, json: async () => ({ rooms: ROOMS }) };
    if (path.startsWith('/api/users')) return { status: 200, json: async () => ({ users: CANDIDATES }) };
    if (path === '/api/reservations' && options.method === 'POST') {
      return { status: 201, json: async () => ({ reservation: { reservation_id: 99 } }) };
    }
    return { status: 204, json: async () => null };
  };
  api.takePendingMessage();
  s03 = await import('../src/views/s03-reservation-new.js');
  s02 = await import('../src/views/s02-calendar.js');
  s02.takeFlash();
});

function errorResponse(status, code, message, extra = {}) {
  return { status, json: async () => ({ error: { code, message, ...extra } }) };
}

function formOf(root) {
  return root.querySelector('[data-role="reservation-form"]');
}

function setField(root, role, value) {
  formOf(root).querySelector(`[data-role="${role}"]`).value = value;
}

async function renderWithQuery() {
  return s03.render({ room_id: '1', date: TOMORROW, start: '14:00' }, app, header);
}

function postCalls() {
  return calls.filter((c) => c.path === '/api/reservations' && c.method === 'POST');
}

test('初期値: クエリの room_id / date / start が反映され、終了は開始+30分', async () => {
  const root = await renderWithQuery();
  const form = formOf(root);
  assert.equal(form.querySelector('[data-role="room_id"]').value, '1');
  assert.equal(form.querySelector('[data-role="reserved_date"]').value, TOMORROW);
  assert.equal(form.querySelector('[data-role="start_time"]').value, '14:00');
  assert.equal(form.querySelector('[data-role="end_time"]').value, '14:30');
});

test('参加者候補が GET /api/users?scope=attendee_candidates から描画される', async () => {
  const root = await renderWithQuery();
  assert.ok(calls.some((c) => c.path === '/api/users?scope=attendee_candidates'));
  assert.deepEqual(
    formOf(root).querySelectorAll('[data-role="attendee_user_ids"] option').map((o) => o.value),
    ['user001', 'user002']
  );
});

test('正常系: 正しい入力で POST が期待するボディで1回だけ呼ばれ、#/calendar へ戻る', async () => {
  const root = await renderWithQuery();
  setField(root, 'title', '打合せ');
  const attendee = formOf(root).querySelectorAll('[data-role="attendee_user_ids"] option')[1];
  attendee.selected = true;
  assert.equal(await s03.submit(root), true);
  assert.equal(postCalls().length, 1);
  assert.deepEqual(postCalls()[0].body, {
    room_id: 1,
    reserved_date: TOMORROW,
    start_time: '14:00',
    end_time: '14:30',
    title: '打合せ',
    attendee_user_ids: ['user002'],
    attendee_count: null,
    meeting_url: '', // ※CR-001 未入力は空文字で送る(null にしない。P002 5.3)
    note: '',
  });
  assert.equal(globalThis.location.hash, '#/calendar');
  assert.equal(s02.takeFlash(), '予約を登録しました。');
});

test('異常系: 件名未入力ならAPIを呼ばず件名欄の直下にエラーが出る', async () => {
  const root = await renderWithQuery();
  setField(root, 'title', '');
  assert.equal(await s03.submit(root), false);
  assert.equal(postCalls().length, 0);
  assert.equal(
    formOf(root).querySelector('[data-error-for="title"]').textContent,
    '件名を入力してください。'
  );
});

test('異常系: 件名101文字ならAPIを呼ばない', async () => {
  const root = await renderWithQuery();
  setField(root, 'title', 'あ'.repeat(101));
  assert.equal(await s03.submit(root), false);
  assert.equal(postCalls().length, 0);
});

test('異常系: 終了 <= 開始 ならAPIを呼ばない', async () => {
  const root = await renderWithQuery();
  setField(root, 'title', '打合せ');
  setField(root, 'start_time', '15:00');
  setField(root, 'end_time', '14:30');
  assert.equal(await s03.submit(root), false);
  assert.equal(postCalls().length, 0);
  assert.equal(
    formOf(root).querySelector('[data-error-for="end_time"]').textContent,
    '終了時刻は開始時刻より後にしてください。'
  );
});

test('異常系: 参加予定人数が収容人数+1 ならAPIを呼ばない', async () => {
  const root = await renderWithQuery();
  setField(root, 'title', '打合せ');
  setField(root, 'room_id', '2');
  setField(root, 'attendee_count', '5');
  assert.equal(await s03.submit(root), false);
  assert.equal(postCalls().length, 0);
  assert.equal(
    formOf(root).querySelector('[data-error-for="attendee_count"]').textContent,
    '参加予定人数が会議室の収容人数(4名)を超えています。'
  );
});

test('異常系: 409 応答で重複エラー領域に競合時間帯が表示される', async () => {
  const root = await renderWithQuery();
  setField(root, 'title', '打合せ');
  responses['POST /api/reservations'] = errorResponse(
    409, 'RESERVATION_CONFLICT', '選択した時間帯はすでに予約されています。',
    { conflicts: [{ reservation_id: 9, start_time: '10:00', end_time: '11:00' }] }
  );
  assert.equal(await s03.submit(root), false);
  const text = formOf(root).querySelector('[data-role="conflict-error"]').textContent;
  assert.ok(text.includes('選択した時間帯はすでに予約されています。'));
  assert.ok(text.includes('10:00-11:00'));
  assert.equal(globalThis.location.hash, ''); // 画面はS03のまま
});

test('異常系: 400 CAPACITY_EXCEEDED が収容人数超過領域に表示される', async () => {
  const root = await renderWithQuery();
  setField(root, 'title', '打合せ');
  responses['POST /api/reservations'] = errorResponse(
    400, 'CAPACITY_EXCEEDED', '参加予定人数が会議室の収容人数(10名)を超えています。'
  );
  assert.equal(await s03.submit(root), false);
  assert.equal(
    formOf(root).querySelector('[data-role="capacity-error"]').textContent,
    '参加予定人数が会議室の収容人数(10名)を超えています。'
  );
});

test('送信中は登録ボタンが非活性になる', async () => {
  const root = await renderWithQuery();
  setField(root, 'title', '打合せ');
  const button = root.querySelector('[data-action="save"]');
  let observed = null;
  responses['POST /api/reservations'] = {
    status: 201,
    json: async () => {
      observed = button.disabled;
      return { reservation: { reservation_id: 99 } };
    },
  };
  await s03.submit(root);
  assert.equal(observed, true);
  assert.equal(button.disabled, false);
});

test('キャンセルは確認なしで #/calendar へ戻る', async () => {
  const root = await renderWithQuery();
  root.querySelector('[data-action="cancel"]').click();
  assert.equal(globalThis.location.hash, '#/calendar');
  assert.equal(postCalls().length, 0);
});

// ※CR-001 オンライン会議URL(P002 3.3)
test('正常系: オンライン会議URLを入力すると送信ボディに含まれる', async () => {
  const root = await renderWithQuery();
  setField(root, 'title', '打合せ');
  setField(root, 'meeting_url', 'https://example.com/meet/t016');
  assert.equal(await s03.submit(root), true);
  assert.equal(postCalls().length, 1);
  assert.equal(postCalls()[0].body.meeting_url, 'https://example.com/meet/t016');
});

test('正常系: オンライン会議URLが空欄でも登録できる(空文字で送る)', async () => {
  const root = await renderWithQuery();
  setField(root, 'title', '打合せ');
  assert.equal(await s03.submit(root), true);
  assert.equal(postCalls()[0].body.meeting_url, '');
});

test('異常系: 不正なオンライン会議URLならAPIを呼ばずフィールド直下にエラーが出る', async () => {
  const root = await renderWithQuery();
  setField(root, 'title', '打合せ');
  setField(root, 'meeting_url', 'example.com/meet');
  assert.equal(await s03.submit(root), false);
  assert.equal(postCalls().length, 0);
  assert.equal(
    formOf(root).querySelector('[data-error-for="meeting_url"]').textContent,
    'オンライン会議URLは http:// または https:// で始まるURLを入力してください。'
  );
});
