// A011 — 利用者視点の受け入れシナリオ(手順1〜6)
// docs/P009-acceptance-direction/A011-user-acceptance.md
// 手順7(実ブラウザでの目視確認)は自動化できないため、テスト記録に NOT RUN として理由を残す。
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
let s05;
let myReservationId;

const TARGET_DATE = addDays(today(), 1);

before(async () => {
  let callJson;
  ({ server, httpFetch, callJson, roomIds } = await startWithBaseData());
  // 既存予約数件(他ユーザー分。空き状況が読み取れることを確認するため)
  assert.equal(
    (await callJson('/api/auth/login', 'POST', { user_id: 'user002', password: PASSWORD })).status,
    200
  );
  for (const [room, start, end, title] of [
    ['会議室A', '09:00', '10:00', '朝会'],
    ['会議室A', '11:00', '12:00', '面談'],
    ['会議室B', '13:00', '14:00', '相談'],
  ]) {
    const res = await callJson('/api/reservations', 'POST', {
      room_id: roomIds[room], reserved_date: TARGET_DATE, start_time: start, end_time: end,
      title, attendee_user_ids: [], attendee_count: null, note: '',
    });
    const payload = await res.json();
    assert.equal(res.status, 201, JSON.stringify(payload));
  }
  httpFetch.clearCookies();

  env = installDom();
  api.runtime.fetch = httpFetch;
  api.runtime.navigate = (hash) => { globalThis.location.hash = hash; };
  s01 = await import('../../src/views/s01-login.js');
  s02 = await import('../../src/views/s02-calendar.js');
  s03 = await import('../../src/views/s03-reservation-new.js');
  s04 = await import('../../src/views/s04-reservation-detail.js');
  s05 = await import('../../src/views/s05-my-reservations.js');
  s02.resetState();
  s02.takeFlash();
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

test('手順1: S02だけを見て、翌営業日に会議室Aが空いている時間帯を特定できる', async () => {
  const form = s01.render({}, env.app, env.header);
  form.querySelector('[name="user_id"]').value = 'user001';
  form.querySelector('[name="password"]').value = PASSWORD;
  assert.equal(await s01.submit(form), true);
  await s02.render({ date: TARGET_DATE }, env.app, env.header);

  // 予約済みセルは「予約者名 / 件名」を表示し、is-reserved が付く(視覚的に区別できる)
  const busy = cell(TARGET_DATE, '会議室A', '09:00');
  assert.equal(busy.textContent, '鈴木 花子 / 朝会');
  assert.ok(busy.className.includes('is-reserved'), busy.className);
  // 空きセルは「+」で、is-reserved が付かない
  const free = cell(TARGET_DATE, '会議室A', '10:00');
  assert.equal(free.textContent, '+');
  assert.ok(!free.className.includes('is-reserved'), free.className);
  // 空き時間帯を機械的に列挙できる(=画面から特定できる)
  const freeSlots = grid()
    .querySelectorAll(
      `[data-role="day-grid"][data-date="${TARGET_DATE}"] [data-cell][data-room-id="${roomIds['会議室A']}"]`
    )
    .filter((c) => c.textContent === '+')
    .map((c) => c.getAttribute('data-slot'));
  assert.ok(freeSlots.includes('10:00'), freeSlots.join(','));
  assert.ok(freeSlots.includes('14:00'), freeSlots.join(','));
  assert.ok(!freeSlots.includes('09:00'), freeSlots.join(','));
});

test('手順2: 空きセルから予約作成がS03だけで完結する', async () => {
  cell(TARGET_DATE, '会議室A', '14:00').click();
  assert.equal(
    globalThis.location.hash,
    `#/reservations/new?room_id=${roomIds['会議室A']}&date=${TARGET_DATE}&start=14:00&end=14:30`
  );
  const root = await s03.render(
    { room_id: String(roomIds['会議室A']), date: TARGET_DATE, start: '14:00', end: '14:30' },
    env.app, env.header
  );
  const form = root.querySelector('[data-role="reservation-form"]');
  form.querySelector('[data-role="title"]').value = '企画会議';
  form.querySelector('[data-role="attendee_count"]').value = '4';
  assert.equal(await s03.submit(root), true);
  assert.equal(globalThis.location.hash, '#/calendar');
});

test('手順3: 重複する時間帯を選ぶと、何が問題かが画面のメッセージから分かる', async () => {
  const root = await s03.render(
    { room_id: String(roomIds['会議室A']), date: TARGET_DATE, start: '09:00', end: '10:00' },
    env.app, env.header
  );
  const form = root.querySelector('[data-role="reservation-form"]');
  form.querySelector('[data-role="title"]').value = 'うっかり重複';
  globalThis.location.hash = '';
  assert.equal(await s03.submit(root), false);
  const text = form.querySelector('[data-role="conflict-error"]').textContent;
  assert.ok(text.includes('選択した時間帯はすでに予約されています。'), text);
  assert.ok(text.includes('09:00-10:00'), `競合時間帯が示されること: ${text}`);
  assert.equal(globalThis.location.hash, '', '画面はS03のまま');
});

test('手順4: 作成した予約をS05から見つけ、S04で時間帯を変更する', async () => {
  const list = await s05.render({}, env.app, env.header);
  const rows = list.querySelectorAll('[data-role="reservation-rows"] tr');
  assert.equal(rows.length, 1, `マイ予約の件数: ${rows.length}`);
  assert.equal(rows[0].querySelector('[data-column="title"]').textContent, '企画会議');
  myReservationId = rows[0].getAttribute('data-reservation-id');
  rows[0].click();
  assert.equal(globalThis.location.hash, `#/reservations/${myReservationId}`);

  const detail = await s04.render({ reservation_id: myReservationId }, env.app, env.header);
  detail.querySelector('[data-action="edit"]').click();
  const form = detail.querySelector('[data-role="reservation-form"]');
  form.querySelector('[data-role="start_time"]').value = '16:00';
  form.querySelector('[data-role="end_time"]').value = '17:00';
  assert.equal(await s04.submit(detail), true);
});

test('手順5: 変更がS02に反映されている', async () => {
  s02.resetState();
  await s02.render({ date: TARGET_DATE }, env.app, env.header);
  assert.equal(grid().querySelector('[data-top-message]').textContent, '予約を更新しました。');
  assert.equal(cell(TARGET_DATE, '会議室A', '14:00').textContent, '+');
  assert.equal(cell(TARGET_DATE, '会議室A', '16:00').textContent, '山田 太郎 / 企画会議');
});

test('手順6: 予約を取り消すとS02とS05の両方から消える', async () => {
  const detail = await s04.render({ reservation_id: myReservationId }, env.app, env.header);
  globalThis.confirm = () => true;
  assert.equal(await s04.remove(detail), true);

  s02.resetState();
  await s02.render({ date: TARGET_DATE }, env.app, env.header);
  assert.equal(cell(TARGET_DATE, '会議室A', '16:00').textContent, '+');

  const list = await s05.render({}, env.app, env.header);
  assert.equal(
    list.querySelector('[data-role="empty-message"]').textContent,
    '該当する予約はありません。'
  );
});
