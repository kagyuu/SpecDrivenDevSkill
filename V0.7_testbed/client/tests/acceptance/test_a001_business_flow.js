// A001 — 予約業務フロー全体(docs/P009-acceptance-direction/A001-reservation-business-flow.md)
// ログイン→カレンダー→作成→詳細→編集→取消の一連を、実サーバープロセスに接続して確認する。
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
let s01;
let s02;
let s03;
let s04;

const TARGET_DATE = addDays(today(), 1);
const MEETING_URL = 'https://example.com/meet/a001'; // ※CR-001
let reservationId;

before(async () => {
  ({ server, httpFetch, roomIds } = await startWithBaseData());
  env = installDom();
  api.runtime.fetch = httpFetch;
  api.runtime.navigate = (hash) => { globalThis.location.hash = hash; };
  s01 = await import('../../src/views/s01-login.js');
  s02 = await import('../../src/views/s02-calendar.js');
  s03 = await import('../../src/views/s03-reservation-new.js');
  s04 = await import('../../src/views/s04-reservation-detail.js');
  s02.resetState();
  s02.takeFlash();
  httpFetch.clearCookies(); // 投入に使った admin001 のセッションを捨てる
});

after(() => { if (server) server.stop(); });

function grid() {
  return env.app.querySelector('[data-view="s02-calendar"]');
}

function cell(date, roomName, slot) {
  return grid().querySelector(
    `[data-cell][data-date="${date}"][data-room-id="${roomIds[roomName]}"][data-slot="${slot}"]`
  );
}

test('手順1: S01で user001 としてログインできる', async () => {
  const form = s01.render({}, env.app, env.header);
  form.querySelector('[name="user_id"]').value = 'user001';
  form.querySelector('[name="password"]').value = PASSWORD;
  assert.equal(await s01.submit(form), true);
  assert.equal(globalThis.location.hash, '#/calendar');
  assert.equal((await httpFetch('/api/me')).status, 200);
});

test('手順2: S02で「本日+1日」の週が表示され、会議室A・Bの列がある', async () => {
  await s02.render({ date: TARGET_DATE }, env.app, env.header);
  const dayGrid = grid().querySelector(`[data-role="day-grid"][data-date="${TARGET_DATE}"]`);
  assert.ok(dayGrid, `${TARGET_DATE} の日付グリッドがある`);
  const headers = dayGrid.querySelectorAll('thead th');
  const names = headers.map((h) => h.textContent);
  assert.ok(names.includes('会議室A'), names.join(','));
  assert.ok(names.includes('会議室B'), names.join(','));
  // 無効な会議室Cは列に現れない
  assert.ok(!names.includes('会議室C'), names.join(','));
  // 一般ユーザーのヘッダーに管理メニューは出ない
  assert.equal(env.header.querySelector('[href="#/admin/rooms"]'), null);
});

test('手順3: 会議室A 13:00 の空きセルをクリックしてS03へ進む', async () => {
  const target = cell(TARGET_DATE, '会議室A', '13:00');
  assert.ok(target, '13:00 のセルがある');
  assert.equal(target.textContent, '+');
  target.click();
  assert.equal(
    globalThis.location.hash,
    `#/reservations/new?room_id=${roomIds['会議室A']}&date=${TARGET_DATE}&start=13:00&end=13:30`
  );
});

test('手順4: 件名・参加者・参加予定人数・備考・オンライン会議URL(※CR-001)を入力して登録する', async () => {
  const root = await s03.render(
    { room_id: String(roomIds['会議室A']), date: TARGET_DATE, start: '13:00', end: '13:30' },
    env.app, env.header
  );
  const form = root.querySelector('[data-role="reservation-form"]');
  form.querySelector('[data-role="title"]').value = '定例会議';
  const attendees = form.querySelector('[data-role="attendee_user_ids"]');
  for (const option of attendees.querySelectorAll('option')) {
    if (option.value === 'user002') option.selected = true;
  }
  form.querySelector('[data-role="attendee_count"]').value = '6';
  form.querySelector('[data-role="note"]').value = '資料は事前配布';
  // ※CR-001 オンライン会議URL
  form.querySelector('[data-role="meeting_url"]').value = MEETING_URL;
  assert.equal(await s03.submit(root), true, '登録が成功すること');
  assert.equal(globalThis.location.hash, '#/calendar');
});

test('手順5: S02に戻り 13:00 に予約が表示され 13:30 は空きのまま(終了時刻は13:30)', async () => {
  s02.resetState();
  await s02.render({ date: TARGET_DATE }, env.app, env.header);
  assert.equal(grid().querySelector('[data-top-message]').textContent, '予約を登録しました。');
  const reserved = cell(TARGET_DATE, '会議室A', '13:00');
  assert.equal(reserved.textContent, '山田 太郎 / 定例会議');
  assert.ok(reserved.className.includes('is-reserved'), reserved.className);
  assert.ok(reserved.className.includes('is-mine'), reserved.className);
  reservationId = reserved.getAttribute('data-reservation-id');
  assert.ok(reservationId);
  // 期待結果(F002で修正): 半開区間 [start, end) のため 13:30 は占有しない(ADR-007)
  const boundary = cell(TARGET_DATE, '会議室A', '13:30');
  assert.equal(boundary.textContent, '+', '13:30 のセルは空きのまま(ADR-007 半開区間)');
  assert.ok(!boundary.className.includes('is-reserved'), boundary.className);
});

test('手順6: 予約セルからS04を開くと入力内容がすべて表示される', async () => {
  cell(TARGET_DATE, '会議室A', '13:00').click();
  assert.equal(globalThis.location.hash, `#/reservations/${reservationId}`);
  const root = await s04.render({ reservation_id: reservationId }, env.app, env.header);
  const value = (field) => root.querySelector(`[data-field="${field}"]`).textContent;
  assert.equal(value('room_name'), '会議室A');
  assert.equal(value('reserved_date'), TARGET_DATE);
  assert.equal(value('time_range'), '13:00-13:30');
  assert.equal(value('title'), '定例会議');
  assert.equal(value('attendees'), '鈴木 花子');
  assert.equal(value('attendee_count'), '6');
  assert.equal(value('note'), '資料は事前配布');
  assert.equal(value('user_name'), '山田 太郎');
  // ※CR-001 オンライン会議URLがクリック可能なリンクとして表示される
  const link = root.querySelector('[data-role="meeting-url-link"]');
  assert.ok(link, 'オンライン会議URLがリンクとして表示される');
  assert.equal(link.getAttribute('href'), MEETING_URL);
  assert.equal(link.textContent, MEETING_URL);
  assert.ok(root.querySelector('[data-action="edit"]'), '予約者本人なので編集ボタンが出る');
});

test('手順7: S04で件名と時間帯(15:00-16:00)を変更して更新する', async () => {
  const root = env.app.querySelector('[data-view="s04-reservation-detail"]');
  root.querySelector('[data-action="edit"]').click();
  const form = root.querySelector('[data-role="reservation-form"]');
  form.querySelector('[data-role="title"]').value = '定例会議(変更)';
  form.querySelector('[data-role="start_time"]').value = '15:00';
  form.querySelector('[data-role="end_time"]').value = '16:00';
  // ※CR-001 オンライン会議URLは編集モードの初期値として引き継がれている
  assert.equal(form.querySelector('[data-role="meeting_url"]').value, MEETING_URL);
  assert.equal(await s04.submit(root), true, '更新が成功すること');
  assert.equal(globalThis.location.hash, '#/calendar');
});

// ※CR-001 更新後もオンライン会議URLが保持されている
test('手順7の続き(※CR-001): 更新後もオンライン会議URLが保持されている', async () => {
  const root = await s04.render({ reservation_id: reservationId }, env.app, env.header);
  const link = root.querySelector('[data-role="meeting-url-link"]');
  assert.ok(link, '更新後もリンクが表示される');
  assert.equal(link.getAttribute('href'), MEETING_URL);
});

test('手順8: S02で 13:00 が空きに戻り、15:00・15:30 に予約が出る', async () => {
  s02.resetState();
  await s02.render({ date: TARGET_DATE }, env.app, env.header);
  assert.equal(grid().querySelector('[data-top-message]').textContent, '予約を更新しました。');
  assert.equal(cell(TARGET_DATE, '会議室A', '13:00').textContent, '+');
  assert.equal(cell(TARGET_DATE, '会議室A', '15:00').textContent, '山田 太郎 / 定例会議(変更)');
  assert.equal(cell(TARGET_DATE, '会議室A', '15:30').textContent, '山田 太郎 / 定例会議(変更)');
  assert.equal(cell(TARGET_DATE, '会議室A', '16:00').textContent, '+');
});

test('手順9: S04を開いて取消する', async () => {
  cell(TARGET_DATE, '会議室A', '15:00').click();
  const root = await s04.render({ reservation_id: reservationId }, env.app, env.header);
  globalThis.confirm = () => true;
  assert.equal(await s04.remove(root), true, '取消が成功すること');
  assert.equal(globalThis.location.hash, '#/calendar');
});

test('手順10: S02で当該時間帯が空きに戻る', async () => {
  s02.resetState();
  await s02.render({ date: TARGET_DATE }, env.app, env.header);
  assert.equal(grid().querySelector('[data-top-message]').textContent, '予約を取り消しました。');
  for (const slot of ['13:00', '15:00', '15:30']) {
    assert.equal(cell(TARGET_DATE, '会議室A', slot).textContent, '+', `${slot} が空きに戻る`);
  }
  const res = await httpFetch(`/api/reservations/${reservationId}`);
  assert.equal(res.status, 404, '取消後は詳細が404');
});
