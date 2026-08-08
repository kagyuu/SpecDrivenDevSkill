// U001-T5 単体テスト — datetime.js(P002 3.2)
import { test } from 'node:test';
import assert from 'node:assert/strict';
import * as dt from '../src/lib/datetime.js';

test('startOfWeek: 週のどの曜日から見ても月曜になる', () => {
  // 2026-08-03(月)〜2026-08-09(日)
  const week = ['2026-08-03', '2026-08-04', '2026-08-05', '2026-08-06', '2026-08-07', '2026-08-08', '2026-08-09'];
  for (const day of week) {
    assert.equal(dt.startOfWeek(day), '2026-08-03', `${day} の週初`);
  }
  assert.equal(dt.startOfWeek('2026-08-10'), '2026-08-10');
});

test('endOfWeek / weekDates', () => {
  assert.equal(dt.endOfWeek('2026-08-05'), '2026-08-09');
  assert.deepEqual(dt.weekDates('2026-08-05'), [
    '2026-08-03', '2026-08-04', '2026-08-05', '2026-08-06', '2026-08-07', '2026-08-08', '2026-08-09',
  ]);
});

test('addDays: 月・年をまたぐ加減算', () => {
  assert.equal(dt.addDays('2026-08-31', 1), '2026-09-01');
  assert.equal(dt.addDays('2026-01-01', -1), '2025-12-31');
  assert.equal(dt.addDays('2026-08-05', 7), '2026-08-12');
});

test('timeOptions: 08:00 開始 20:00 終了で25要素', () => {
  const list = dt.timeOptions();
  assert.equal(list.length, 25);
  assert.equal(list[0], '08:00');
  assert.equal(list[1], '08:30');
  assert.equal(list[list.length - 1], '20:00');
});

test('toMinutes / formatTime / addMinutes', () => {
  assert.equal(dt.toMinutes('09:30'), 570);
  assert.equal(dt.formatTime(570), '09:30');
  assert.equal(dt.addMinutes('09:00', 30), '09:30');
  assert.equal(dt.addMinutes('19:30', 30), '20:00');
});
