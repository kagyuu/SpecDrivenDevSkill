// U004-T1 単体テスト — grid.js(占有マップの構築。P002 3.2)
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { buildOccupancy, cellLabel, filterRooms, occupiedSlots, reservationAt, slotKey } from '../src/lib/grid.js';
import { timeOptions } from '../src/lib/datetime.js';

const SLOTS = timeOptions('08:00', '19:30');

function reservation(overrides = {}) {
  return {
    reservation_id: 1,
    room_id: 1,
    room_name: '会議室A',
    user_id: 'user001',
    user_name: '山田 太郎',
    reserved_date: '2026-08-10',
    start_time: '09:00',
    end_time: '10:00',
    title: '定例会議',
    attendee_count: 8,
    ...overrides,
  };
}

test('09:00-10:00 の予約は 09:00 と 09:30 のみを占有する(終了スロットは占有しない)', () => {
  assert.deepEqual(occupiedSlots(reservation(), SLOTS), ['09:00', '09:30']);
});

test('長い予約は開始から終了直前までのスロットを占有する', () => {
  assert.deepEqual(
    occupiedSlots(reservation({ start_time: '13:00', end_time: '15:00' }), SLOTS),
    ['13:00', '13:30', '14:00', '14:30']
  );
});

test('30分の予約は1スロットだけ占有する', () => {
  assert.deepEqual(
    occupiedSlots(reservation({ start_time: '18:00', end_time: '18:30' }), SLOTS),
    ['18:00']
  );
});

test('buildOccupancy: 10:00 スロットは空きのままになる', () => {
  const map = buildOccupancy([reservation()], SLOTS);
  assert.ok(reservationAt(map, '2026-08-10', 1, '09:00'));
  assert.ok(reservationAt(map, '2026-08-10', 1, '09:30'));
  assert.equal(reservationAt(map, '2026-08-10', 1, '10:00'), null);
});

test('buildOccupancy: 複数会議室・複数日で正しい位置に入る', () => {
  const map = buildOccupancy(
    [
      reservation(),
      reservation({ reservation_id: 2, room_id: 2, start_time: '11:00', end_time: '11:30' }),
      reservation({ reservation_id: 3, reserved_date: '2026-08-11', start_time: '09:00', end_time: '09:30' }),
    ],
    SLOTS
  );
  assert.equal(reservationAt(map, '2026-08-10', 1, '09:00').reservation_id, 1);
  assert.equal(reservationAt(map, '2026-08-10', 2, '11:00').reservation_id, 2);
  assert.equal(reservationAt(map, '2026-08-10', 2, '09:00'), null);
  assert.equal(reservationAt(map, '2026-08-11', 1, '09:00').reservation_id, 3);
});

test('buildOccupancy: 予約0件なら全セルが空き', () => {
  const map = buildOccupancy([], SLOTS);
  assert.equal(map.size, 0);
  assert.equal(reservationAt(map, '2026-08-10', 1, '09:00'), null);
});

test('slotKey は (日付, 会議室, スロット) を一意に表す', () => {
  assert.equal(slotKey('2026-08-10', 1, '09:00'), '2026-08-10|1|09:00');
});

test('filterRooms: 未選択なら全件、選択があれば絞り込む', () => {
  const rooms = [{ room_id: 1 }, { room_id: 2 }, { room_id: 3 }];
  assert.equal(filterRooms(rooms, []).length, 3);
  assert.deepEqual(filterRooms(rooms, [2]).map((r) => r.room_id), [2]);
  assert.deepEqual(filterRooms(rooms, ['1', '3']).map((r) => r.room_id), [1, 3]);
});

test('cellLabel: 空きは +、予約済みは「予約者の氏名 / 件名」で参加予定人数を含まない', () => {
  assert.equal(cellLabel(null), '+');
  const label = cellLabel(reservation());
  assert.equal(label, '山田 太郎 / 定例会議');
  assert.equal(label.includes('8'), false);
});

// ※CR-001 退行確認: S02のセル表示にオンライン会議URLを混入させない(CR-001が明示的に対象外)
test('cellLabel: オンライン会議URLはセル表示に含まれない', () => {
  const url = 'https://example.com/meet/abc';
  const label = cellLabel(reservation({ meeting_url: url }));
  assert.equal(label, '山田 太郎 / 定例会議');
  assert.equal(label.includes('http'), false);
  assert.equal(label.includes(url), false);
});
