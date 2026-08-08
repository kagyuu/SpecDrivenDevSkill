// T017 — S04の編集・取消と権限による表示制御(docs/P008-test-direction/T017-detail-edit-cancel.md)
// 実サーバー(uvicorn)に対して実行する。
import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import { installDom } from '../helpers/dom-env.js';
import { startServer, makeFetch } from '../helpers/server.js';
import * as api from '../../src/lib/api.js';
import { addDays, today } from '../../src/lib/datetime.js';

let server;
let httpFetch;
let s04;
let s02;
let env;
let calls;
const rooms = {};
let primaryId;
let secondaryId;

const TOMORROW = addDays(today(), 1);

async function callJson(path, method, body) {
  const options = { method, headers: { 'Content-Type': 'application/json' } };
  if (body) options.body = JSON.stringify(body);
  return httpFetch(path, options);
}

async function loginAs(userId) {
  const res = await callJson('/api/auth/login', 'POST', { user_id: userId, password: 'Passw0rd!23' });
  assert.equal(res.status, 200);
}

before(async () => {
  server = await startServer();
  httpFetch = makeFetch(server.baseUrl);
  await loginAs('admin001');
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
  await loginAs('user001');
  const created = await callJson('/api/reservations', 'POST', {
    room_id: rooms['会議室A'], reserved_date: TOMORROW, start_time: '10:00', end_time: '11:00',
    title: '定例会議', attendee_user_ids: ['user002'], attendee_count: null, note: '資料は事前配布',
  });
  assert.equal(created.status, 201);
  primaryId = (await created.json()).reservation.reservation_id;
  // 手順5・6 で使う「user001 の別の予約」
  const second = await callJson('/api/reservations', 'POST', {
    room_id: rooms['会議室B'], reserved_date: TOMORROW, start_time: '15:00', end_time: '16:00',
    title: '別の予約', attendee_user_ids: [], attendee_count: null, note: '',
  });
  assert.equal(second.status, 201);
  secondaryId = (await second.json()).reservation.reservation_id;

  env = installDom();
  calls = [];
  api.runtime.fetch = async (path, options) => {
    calls.push({ path, method: options.method });
    return httpFetch(path, options);
  };
  api.runtime.navigate = (hash) => { globalThis.location.hash = hash; };
  globalThis.confirm = () => true;
  s04 = await import('../../src/views/s04-reservation-detail.js');
  s02 = await import('../../src/views/s02-calendar.js');
  s02.takeFlash();
});

after(() => { if (server) server.stop(); });

const open = (id) => s04.render({ reservation_id: String(id) }, env.app, env.header);

test('手順1: user001 でS04を開くと表示項目が揃い、編集・取消ボタンがある', async () => {
  await loginAs('user001');
  const root = await open(primaryId);
  const value = (field) => root.querySelector(`[data-field="${field}"]`).textContent;
  assert.equal(value('room_name'), '会議室A');
  assert.equal(value('reserved_date'), TOMORROW);
  assert.equal(value('time_range'), '10:00-11:00');
  assert.equal(value('title'), '定例会議');
  assert.equal(value('attendees'), '鈴木 花子');
  assert.equal(value('attendee_count'), '-');
  // ※CR-001: 基準データセットの予約はオンライン会議URL未登録なので「-」
  assert.equal(value('meeting_url'), '-');
  assert.equal(root.querySelector('[data-role="meeting-url-link"]'), null);
  assert.equal(value('note'), '資料は事前配布');
  assert.equal(value('user_name'), '山田 太郎');
  assert.ok(root.querySelector('[data-action="edit"]'));
  assert.ok(root.querySelector('[data-action="delete"]'));
});

test('手順2: 件名を「臨時会議」に変更して更新すると PUT が呼ばれ #/calendar へ戻る', async () => {
  const root = env.app.querySelector('[data-view="s04-reservation-detail"]');
  root.querySelector('[data-action="edit"]').click();
  root.querySelector('[data-role="reservation-form"]')
    .querySelector('[data-role="title"]').value = '臨時会議';
  assert.equal(await s04.submit(root), true);
  assert.ok(calls.some((c) => c.method === 'PUT' && c.path === `/api/reservations/${primaryId}`));
  assert.equal(globalThis.location.hash, '#/calendar');
  assert.equal(s02.takeFlash(), '予約を更新しました。');
  const reloaded = await (await callJson(`/api/reservations/${primaryId}`, 'GET')).json();
  assert.equal(reloaded.reservation.title, '臨時会議');
});

test('手順3: 取消の確認でキャンセルすると DELETE が呼ばれない', async () => {
  const root = await open(primaryId);
  globalThis.confirm = () => false;
  const before = calls.filter((c) => c.method === 'DELETE').length;
  assert.equal(await s04.remove(root), false);
  assert.equal(calls.filter((c) => c.method === 'DELETE').length, before);
});

test('手順4: 取消の確認でOKなら DELETE が呼ばれ #/calendar へ戻る', async () => {
  const root = env.app.querySelector('[data-view="s04-reservation-detail"]');
  globalThis.confirm = () => true;
  assert.equal(await s04.remove(root), true);
  assert.ok(calls.some((c) => c.method === 'DELETE' && c.path === `/api/reservations/${primaryId}`));
  assert.equal(globalThis.location.hash, '#/calendar');
  assert.equal(s02.takeFlash(), '予約を取り消しました。');
  assert.equal((await callJson(`/api/reservations/${primaryId}`, 'GET')).status, 404);
});

test('手順5: user002 では詳細は見えるが編集・取消ボタンが無い', async () => {
  await loginAs('user002');
  const root = await open(secondaryId);
  assert.equal(root.querySelector('[data-field="title"]').textContent, '別の予約');
  assert.equal(root.querySelector('[data-action="edit"]'), null);
  assert.equal(root.querySelector('[data-action="delete"]'), null);
});

test('手順6: admin001 では編集・取消ボタンが表示される', async () => {
  await loginAs('admin001');
  const root = await open(secondaryId);
  assert.ok(root.querySelector('[data-action="edit"]'));
  assert.ok(root.querySelector('[data-action="delete"]'));
});

test('手順7: 存在しない reservation_id では NOT_FOUND のメッセージが出る', async () => {
  const root = await open(999999);
  assert.equal(
    root.querySelector('[data-top-message]').textContent,
    '対象のデータが見つかりません。削除された可能性があります。'
  );
});

// ※CR-001 手順8〜10(オンライン会議URLのリンク表示と編集)
let urlReservationId;

test('手順8: オンライン会議URL登録済みの予約はクリック可能なリンクとして表示される', async () => {
  await loginAs('user001');
  const url = 'https://example.com/meet/t017';
  const created = await callJson('/api/reservations', 'POST', {
    room_id: rooms['会議室A'], reserved_date: TOMORROW, start_time: '13:00', end_time: '14:00',
    title: 'オンライン会議', attendee_user_ids: [], attendee_count: null,
    meeting_url: url, note: '',
  });
  assert.equal(created.status, 201);
  urlReservationId = (await created.json()).reservation.reservation_id;

  const root = await open(urlReservationId);
  const link = root.querySelector('[data-role="meeting-url-link"]');
  assert.ok(link, 'リンクが描画されている');
  assert.equal(link.tagName, 'A');
  assert.equal(link.getAttribute('href'), url);
  assert.equal(link.textContent, url);
  assert.equal(link.getAttribute('target'), '_blank');
  assert.equal(link.getAttribute('rel'), 'noopener noreferrer');
});

test('手順9: 編集モードの初期値がURLで、空欄にして更新するとURLが削除される', async () => {
  const root = env.app.querySelector('[data-view="s04-reservation-detail"]');
  root.querySelector('[data-action="edit"]').click();
  const formEl = root.querySelector('[data-role="reservation-form"]');
  assert.equal(
    formEl.querySelector('[data-role="meeting_url"]').value,
    'https://example.com/meet/t017'
  );
  formEl.querySelector('[data-role="meeting_url"]').value = '';
  assert.equal(await s04.submit(root), true);
  const stored = await (await callJson(`/api/reservations/${urlReservationId}`, 'GET')).json();
  assert.equal(stored.reservation.meeting_url, '');
  s02.takeFlash();

  const reopened = await open(urlReservationId);
  assert.equal(reopened.querySelector('[data-field="meeting_url"]').textContent, '-');
  assert.equal(reopened.querySelector('[data-role="meeting-url-link"]'), null);
});

test('手順10: 不正なオンライン会議URLでの更新はPUTを呼ばず欄の直下にエラーが出る', async () => {
  const root = env.app.querySelector('[data-view="s04-reservation-detail"]');
  root.querySelector('[data-action="edit"]').click();
  const formEl = root.querySelector('[data-role="reservation-form"]');
  formEl.querySelector('[data-role="meeting_url"]').value = 'example.com/meet';
  const before = calls.filter(
    (c) => c.method === 'PUT' && c.path === `/api/reservations/${urlReservationId}`
  ).length;
  assert.equal(await s04.submit(root), false);
  assert.equal(
    calls.filter(
      (c) => c.method === 'PUT' && c.path === `/api/reservations/${urlReservationId}`
    ).length,
    before,
    'PUT が呼ばれないこと'
  );
  assert.equal(
    formEl.querySelector('[data-error-for="meeting_url"]').textContent,
    'オンライン会議URLは http:// または https:// で始まるURLを入力してください。'
  );
});
