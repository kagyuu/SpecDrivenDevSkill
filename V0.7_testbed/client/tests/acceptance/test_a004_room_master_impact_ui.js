// A004 — 会議室マスタ変更の予約への波及(画面側 手順6・8・9)
// docs/P009-acceptance-direction/A004-room-master-impact.md
// API側は server/tests/acceptance/test_a004_room_master_impact.py が確認する。
import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import { installDom } from '../helpers/dom-env.js';
import { newSession, startWithBaseData, PASSWORD } from './support.js';
import * as api from '../../src/lib/api.js';
import { addDays, today } from '../../src/lib/datetime.js';

let server;
let httpFetch;
let roomIds;
let env;
let s02;
let s03;
let admin;
let reservationId;

const TARGET_DATE = addDays(today(), 1);

before(async () => {
  let callJson;
  ({ server, httpFetch, callJson, roomIds } = await startWithBaseData());

  // 事前準備2: user001 で会議室Aに予約(参加予定人数 8)
  assert.equal(
    (await callJson('/api/auth/login', 'POST', { user_id: 'user001', password: PASSWORD })).status,
    200
  );
  const res = await callJson('/api/reservations', 'POST', {
    room_id: roomIds['会議室A'], reserved_date: TARGET_DATE, start_time: '10:00', end_time: '11:00',
    title: '既存予約', attendee_user_ids: [], attendee_count: 8, note: '',
  });
  const payload = await res.json();
  assert.equal(res.status, 201, JSON.stringify(payload));
  reservationId = payload.reservation.reservation_id;

  // 事前準備3: admin001 は別セッションで保持する
  admin = newSession(server);
  assert.equal(
    (await admin.callJson('/api/auth/login', 'POST', { user_id: 'admin001', password: PASSWORD })).status,
    200
  );
  // 手順2: 収容人数 10 → 5
  const updated = await admin.callJson('/api/rooms/' + roomIds['会議室A'], 'PUT', {
    name: '会議室A', capacity: 5, equipment: 'プロジェクタ', description: '',
  });
  assert.equal(updated.status, 200, JSON.stringify(await updated.json()));

  env = installDom();
  api.runtime.fetch = httpFetch; // 画面は user001 のセッションで動かす
  api.runtime.navigate = (hash) => { globalThis.location.hash = hash; };
  s02 = await import('../../src/views/s02-calendar.js');
  s03 = await import('../../src/views/s03-reservation-new.js');
  s02.resetState();
  s02.takeFlash();
});

after(() => { if (server) server.stop(); });

function roomOptions(form) {
  return form.querySelectorAll('[data-role="room_id"] option').map((o) => o.textContent);
}

test('手順6: S03の会議室プルダウンに会議室Aが出て、収容人数5で検証される', async () => {
  const root = await s03.render(
    { room_id: String(roomIds['会議室A']), date: TARGET_DATE, start: '14:00', end: '15:00' },
    env.app, env.header
  );
  const form = root.querySelector('[data-role="reservation-form"]');
  assert.ok(roomOptions(form).includes('会議室A'), roomOptions(form).join(','));

  // 参加予定人数 6 は収容人数 5 を超えるため、クライアント側検証でエラーになる(P002 3.3)
  form.querySelector('[data-role="title"]').value = '検証';
  form.querySelector('[data-role="attendee_count"]').value = '6';
  assert.equal(await s03.submit(root), false, '収容人数超過で登録できないこと');
  assert.equal(
    form.querySelector('[data-error-for="attendee_count"]').textContent,
    '参加予定人数が会議室の収容人数(5名)を超えています。'
  );

  // 参加予定人数 5(境界値)は通る
  form.querySelector('[data-role="attendee_count"]').value = '5';
  assert.equal(await s03.submit(root), true, '収容人数と同数なら登録できること');
});

test('手順7: 予約をすべて取り消してから会議室Aを無効化できる', async () => {
  // 手順6で作った予約と、事前準備の予約を取り消す
  const mine = await (await httpFetch('/api/reservations/mine?period=upcoming')).json();
  for (const reservation of mine.reservations) {
    const res = await httpFetch(`/api/reservations/${reservation.reservation_id}`, { method: 'DELETE' });
    assert.equal(res.status, 204);
  }
  const res = await admin.callJson('/api/rooms/' + roomIds['会議室A'], 'DELETE');
  assert.equal(res.status, 204, '無効化が成功すること');
});

test('手順8: S03のプルダウンに会議室Aが現れない', async () => {
  const root = await s03.render({ date: TARGET_DATE }, env.app, env.header);
  const form = root.querySelector('[data-role="reservation-form"]');
  const names = roomOptions(form);
  assert.ok(!names.includes('会議室A'), names.join(','));
  assert.ok(names.includes('会議室B'), names.join(','));
});

test('手順9: S02のグリッドに会議室Aの列が現れない', async () => {
  s02.resetState();
  const root = await s02.render({ date: TARGET_DATE }, env.app, env.header);
  const dayGrid = root.querySelector(`[data-role="day-grid"][data-date="${TARGET_DATE}"]`);
  const names = dayGrid.querySelectorAll('thead th').map((h) => h.textContent);
  assert.ok(!names.includes('会議室A'), names.join(','));
  assert.ok(names.includes('会議室B'), names.join(','));
  assert.equal(
    dayGrid.querySelector(`[data-cell][data-room-id="${roomIds['会議室A']}"]`),
    null,
    '会議室Aのセルが存在しない'
  );
});
