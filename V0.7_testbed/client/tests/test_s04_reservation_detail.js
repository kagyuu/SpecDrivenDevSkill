// U004-T3 単体テスト — S04 予約詳細・編集画面(P002 3.4 / 2.4)
import { test, beforeEach } from 'node:test';
import assert from 'node:assert/strict';
import { installDom } from './helpers/dom-env.js';
import * as api from '../src/lib/api.js';
import { addDays, today } from '../src/lib/datetime.js';

let s04;
let s02;
let app;
let header;
let calls;
let responses;
let currentMe;
let currentReservation;
let confirmResult;

const OWNER = { user_id: 'user001', name: '山田 太郎', role: 'general' };
const OTHER = { user_id: 'user002', name: '鈴木 花子', role: 'general' };
const ADMIN = { user_id: 'admin001', name: '管理 太郎', role: 'admin' };
const ROOMS = [
  { room_id: 1, name: '会議室A', capacity: 10, is_active: true },
  { room_id: 2, name: '会議室B', capacity: 4, is_active: true },
];
const CANDIDATES = [
  { user_id: 'user001', name: '山田 太郎' },
  { user_id: 'user002', name: '鈴木 花子' },
];
const TOMORROW = addDays(today(), 1);

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
    attendee_count: null,
    meeting_url: '', // ※CR-001 既定は未登録(空文字)
    note: '資料は事前配布',
    attendees: [{ user_id: 'user002', name: '鈴木 花子' }],
    created_at: '2026-08-01T01:00:00Z',
    updated_at: '2026-08-01T01:00:00Z',
    ...overrides,
  };
}

beforeEach(async () => {
  const env = installDom();
  app = env.app;
  header = env.header;
  calls = [];
  responses = {};
  currentMe = OWNER;
  currentReservation = reservation();
  confirmResult = true;
  globalThis.confirm = () => confirmResult;
  api.runtime.navigate = (hash) => { globalThis.location.hash = hash; };
  api.runtime.fetch = async (path, options) => {
    calls.push({ path, method: options.method, body: options.body ? JSON.parse(options.body) : null });
    const canned = responses[`${options.method} ${path}`];
    if (canned) return canned;
    if (path === '/api/me') return { status: 200, json: async () => ({ user: currentMe }) };
    if (path.startsWith('/api/rooms')) return { status: 200, json: async () => ({ rooms: ROOMS }) };
    if (path.startsWith('/api/users')) return { status: 200, json: async () => ({ users: CANDIDATES }) };
    if (path.startsWith('/api/reservations/') && options.method === 'GET') {
      return { status: 200, json: async () => ({ reservation: currentReservation }) };
    }
    if (options.method === 'PUT') {
      return { status: 200, json: async () => ({ reservation: currentReservation }) };
    }
    return { status: 204, json: async () => null };
  };
  api.takePendingMessage();
  s04 = await import('../src/views/s04-reservation-detail.js');
  s02 = await import('../src/views/s02-calendar.js');
  s02.takeFlash();
});

function errorResponse(status, code, message, extra = {}) {
  return { status, json: async () => ({ error: { code, message, ...extra } }) };
}

const open = () => s04.render({ reservation_id: '12' }, app, header);

test('閲覧: 表示項目が揃い、参加予定人数の未設定は「-」になる', async () => {
  const root = await open();
  const value = (field) => root.querySelector(`[data-field="${field}"]`).textContent;
  assert.equal(value('room_name'), '会議室A');
  assert.equal(value('reserved_date'), TOMORROW);
  assert.equal(value('time_range'), '10:00-11:00');
  assert.equal(value('title'), '定例会議');
  assert.equal(value('attendees'), '鈴木 花子');
  assert.equal(value('attendee_count'), '-');
  assert.equal(value('note'), '資料は事前配布');
  assert.equal(value('user_name'), '山田 太郎');
  assert.ok(value('created_at'));
  assert.ok(value('updated_at'));
});

test('権限: 予約者本人には編集・取消ボタンが出る', async () => {
  const root = await open();
  assert.ok(root.querySelector('[data-action="edit"]'));
  assert.ok(root.querySelector('[data-action="delete"]'));
});

test('権限: 管理者にも編集・取消ボタンが出る', async () => {
  currentMe = ADMIN;
  const root = await open();
  assert.ok(root.querySelector('[data-action="edit"]'));
  assert.ok(root.querySelector('[data-action="delete"]'));
});

test('権限: 第三者には編集・取消ボタンが出ない(閲覧はできる)', async () => {
  currentMe = OTHER;
  const root = await open();
  assert.equal(root.querySelector('[data-action="edit"]'), null);
  assert.equal(root.querySelector('[data-action="delete"]'), null);
  assert.equal(root.querySelector('[data-field="title"]').textContent, '定例会議');
});

test('過去日: 予約者本人でもボタンが出ず「過去の予約は編集できません。」が出る', async () => {
  currentReservation = reservation({ reserved_date: addDays(today(), -1) });
  const root = await open();
  assert.equal(root.querySelector('[data-action="edit"]'), null);
  assert.equal(root.querySelector('[data-action="delete"]'), null);
  assert.equal(
    root.querySelector('[data-role="past-message"]').textContent,
    '過去の予約は編集できません。'
  );
});

test('編集: 既存値が初期値として入り、更新で PUT が正しいボディで呼ばれる', async () => {
  const root = await open();
  root.querySelector('[data-action="edit"]').click();
  const form = root.querySelector('[data-role="reservation-form"]');
  assert.equal(form.querySelector('[data-role="title"]').value, '定例会議');
  assert.equal(form.querySelector('[data-role="room_id"]').value, '1');
  assert.deepEqual(
    form.querySelectorAll('[data-role="attendee_user_ids"] option')
      .filter((o) => o.selected).map((o) => o.value),
    ['user002']
  );
  form.querySelector('[data-role="title"]').value = '臨時会議';
  assert.equal(await s04.submit(root), true);
  const put = calls.find((c) => c.method === 'PUT');
  assert.equal(put.path, '/api/reservations/12');
  assert.equal(put.body.title, '臨時会議');
  assert.deepEqual(put.body.attendee_user_ids, ['user002']);
  assert.equal(globalThis.location.hash, '#/calendar');
  assert.equal(s02.takeFlash(), '予約を更新しました。');
});

test('取消: 確認でキャンセルすると DELETE が呼ばれない', async () => {
  const root = await open();
  confirmResult = false;
  assert.equal(await s04.remove(root), false);
  assert.equal(calls.filter((c) => c.method === 'DELETE').length, 0);
});

test('取消: 確認でOKなら DELETE が呼ばれて #/calendar へ戻る', async () => {
  const root = await open();
  confirmResult = true;
  assert.equal(await s04.remove(root), true);
  assert.equal(calls.filter((c) => c.method === 'DELETE').length, 1);
  assert.equal(globalThis.location.hash, '#/calendar');
  assert.equal(s02.takeFlash(), '予約を取り消しました。');
});

test('異常系: 404 で「対象のデータが見つかりません。削除された可能性があります。」が出る', async () => {
  responses['GET /api/reservations/999'] = errorResponse(
    404, 'NOT_FOUND', '対象のデータが見つかりません。削除された可能性があります。'
  );
  const root = await s04.render({ reservation_id: '999' }, app, header);
  assert.equal(
    root.querySelector('[data-top-message]').textContent,
    '対象のデータが見つかりません。削除された可能性があります。'
  );
});

test('異常系: 409 RESERVATION_CONFLICT で重複エラーが表示される', async () => {
  const root = await open();
  root.querySelector('[data-action="edit"]').click();
  responses['PUT /api/reservations/12'] = errorResponse(
    409, 'RESERVATION_CONFLICT', '選択した時間帯はすでに予約されています。',
    { conflicts: [{ reservation_id: 9, start_time: '10:30', end_time: '11:30' }] }
  );
  assert.equal(await s04.submit(root), false);
  const text = root.querySelector('[data-role="conflict-error"]').textContent;
  assert.ok(text.includes('選択した時間帯はすでに予約されています。'));
  assert.ok(text.includes('10:30-11:30'));
});

test('キャンセル: 遷移元が不明なら #/calendar へ戻る', async () => {
  const root = await open();
  root.querySelector('[data-action="cancel"]').click();
  assert.equal(globalThis.location.hash, '#/calendar');
});

test('キャンセル: 遷移元(S05)が指定されていればそこへ戻る', async () => {
  const root = await s04.render(
    { reservation_id: '12', from: '#/my-reservations' }, app, header
  );
  root.querySelector('[data-action="cancel"]').click();
  assert.equal(globalThis.location.hash, '#/my-reservations');
});

// ※CR-001 オンライン会議URL(P002 3.4)
test('閲覧: オンライン会議URLが未登録なら「-」でリンクを作らない', async () => {
  const root = await open();
  const value = root.querySelector('[data-field="meeting_url"]');
  assert.equal(value.textContent, '-');
  assert.equal(root.querySelector('[data-role="meeting-url-link"]'), null);
});

test('閲覧: オンライン会議URLが登録済みならクリック可能なリンクになる', async () => {
  const url = 'https://example.com/meet/abc';
  currentReservation = reservation({ meeting_url: url });
  const root = await open();
  const link = root.querySelector('[data-role="meeting-url-link"]');
  assert.ok(link);
  assert.equal(link.tagName, 'A');
  assert.equal(link.getAttribute('href'), url);
  assert.equal(link.textContent, url);
  assert.equal(link.getAttribute('target'), '_blank');
  assert.equal(link.getAttribute('rel'), 'noopener noreferrer');
});

test('閲覧: オンライン会議URLの行は参加予定人数と備考の間にある', async () => {
  const root = await open();
  const fields = root
    .querySelectorAll('[data-field]')
    .map((n) => n.getAttribute('data-field'));
  const url = fields.indexOf('meeting_url');
  assert.ok(url > 0);
  assert.ok(fields.indexOf('attendee_count') < url);
  assert.ok(url < fields.indexOf('note'));
});

test('編集: 既存のオンライン会議URLが入力欄の初期値になる', async () => {
  const url = 'https://example.com/meet/abc';
  currentReservation = reservation({ meeting_url: url });
  const root = await open();
  const formEl = s04.openEdit(root);
  assert.equal(formEl.querySelector('[data-role="meeting_url"]').value, url);
});

test('編集: オンライン会議URLを空欄にして更新すると空文字で送信される', async () => {
  currentReservation = reservation({ meeting_url: 'https://example.com/meet/abc' });
  const root = await open();
  const formEl = s04.openEdit(root);
  formEl.querySelector('[data-role="meeting_url"]').value = '';
  assert.equal(await s04.submit(root), true);
  const put = calls.filter((c) => c.method === 'PUT');
  assert.equal(put.length, 1);
  assert.equal(put[0].body.meeting_url, '');
});

test('編集: 不正なオンライン会議URLならAPIを呼ばずフィールド直下にエラーが出る', async () => {
  const root = await open();
  const formEl = s04.openEdit(root);
  formEl.querySelector('[data-role="meeting_url"]').value = 'example.com/meet';
  assert.equal(await s04.submit(root), false);
  assert.equal(calls.filter((c) => c.method === 'PUT').length, 0);
  assert.equal(
    formEl.querySelector('[data-error-for="meeting_url"]').textContent,
    'オンライン会議URLは http:// または https:// で始まるURLを入力してください。'
  );
});
