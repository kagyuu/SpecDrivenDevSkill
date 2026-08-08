// U004-T2 単体テスト — reservation-form.js(S03/S04共有の入力フォーム。P002 3.3)
import { test, beforeEach } from 'node:test';
import assert from 'node:assert/strict';
import { installDom } from './helpers/dom-env.js';
import * as form from '../src/components/reservation-form.js';
import { addDays, today } from '../src/lib/datetime.js';

const ROOMS = [
  { room_id: 1, name: '会議室A', capacity: 10, is_active: true },
  { room_id: 2, name: '会議室B', capacity: 4, is_active: true },
];
const CANDIDATES = [
  { user_id: 'user001', name: '山田 太郎' },
  { user_id: 'user002', name: '鈴木 花子' },
];
const TOMORROW = addDays(today(), 1);

let formEl;

beforeEach(() => {
  installDom();
  formEl = form.buildForm({ rooms: ROOMS, candidates: CANDIDATES });
});

function fill(values) {
  form.setValues(formEl, {
    room_id: 1, reserved_date: TOMORROW, start_time: '10:00', end_time: '11:00',
    title: '打合せ', attendee_user_ids: [], attendee_count: '', note: '', ...values,
  });
}

test('構成: 会議室プルダウンに有効な会議室が並ぶ(先頭は未選択)', () => {
  const options = formEl.querySelectorAll('[data-role="room_id"] option');
  assert.equal(options.length, 3);
  assert.equal(options[0].value, '');
  assert.equal(options[1].textContent, '会議室A');
});

test('構成: 参加者候補が描画される', () => {
  const options = formEl.querySelectorAll('[data-role="attendee_user_ids"] option');
  assert.deepEqual(options.map((o) => o.value), ['user001', 'user002']);
});

test('構成: 時刻は30分刻みのプルダウン(開始 08:00〜19:30 / 終了 08:30〜20:00)', () => {
  const starts = formEl.querySelectorAll('[data-role="start_time"] option').map((o) => o.value);
  const ends = formEl.querySelectorAll('[data-role="end_time"] option').map((o) => o.value);
  assert.equal(starts[0], '08:00');
  assert.equal(starts[starts.length - 1], '19:30');
  assert.equal(ends[0], '08:30');
  assert.equal(ends[ends.length - 1], '20:00');
  assert.ok(starts.every((v) => v.endsWith(':00') || v.endsWith(':30')));
});

test('終日チェックで 09:00 / 18:00 が自動入力される', () => {
  fill({ start_time: '14:00', end_time: '14:30' });
  const allDay = formEl.querySelector('[data-role="all_day"]');
  allDay.checked = true;
  allDay.dispatchEvent({ type: 'change', target: allDay });
  assert.equal(formEl.querySelector('[data-role="start_time"]').value, '09:00');
  assert.equal(formEl.querySelector('[data-role="end_time"]').value, '18:00');
});

test('終日チェック後に開始を手動変更しても保持され、チェックは外れない', () => {
  fill({});
  const allDay = formEl.querySelector('[data-role="all_day"]');
  allDay.checked = true;
  allDay.dispatchEvent({ type: 'change', target: allDay });
  formEl.querySelector('[data-role="start_time"]').value = '10:00';
  assert.equal(formEl.querySelector('[data-role="start_time"]').value, '10:00');
  assert.equal(allDay.checked, true);
});

test('終日チェックを外しても時刻は元に戻らない', () => {
  fill({ start_time: '14:00', end_time: '14:30' });
  const allDay = formEl.querySelector('[data-role="all_day"]');
  allDay.checked = true;
  allDay.dispatchEvent({ type: 'change', target: allDay });
  allDay.checked = false;
  allDay.dispatchEvent({ type: 'change', target: allDay });
  assert.equal(formEl.querySelector('[data-role="start_time"]').value, '09:00');
  assert.equal(formEl.querySelector('[data-role="end_time"]').value, '18:00');
});

test('参加者の選択が読み書きできる', () => {
  fill({ attendee_user_ids: ['user002'] });
  assert.deepEqual(form.readValues(formEl).attendee_user_ids, ['user002']);
});

test('toBody: 数値変換され、参加予定人数の未入力は null になる', () => {
  fill({ attendee_user_ids: ['user002'], note: 'メモ' });
  assert.deepEqual(form.toBody(formEl), {
    room_id: 1,
    reserved_date: TOMORROW,
    start_time: '10:00',
    end_time: '11:00',
    title: '打合せ',
    attendee_user_ids: ['user002'],
    attendee_count: null,
    meeting_url: '', // ※CR-001 未入力は空文字で送る(null にしない。P002 5.3)
    note: 'メモ',
  });
});

test('検証: 件名未入力・101文字はエラー', () => {
  fill({ title: '' });
  assert.equal(form.validate(formEl, today()).title, '件名を入力してください。');
  fill({ title: 'あ'.repeat(101) });
  assert.equal(form.validate(formEl, today()).title, '件名は100文字以内で入力してください。');
});

test('検証: 終了 <= 開始 はエラー', () => {
  fill({ start_time: '11:00', end_time: '10:00' });
  assert.equal(form.validate(formEl, today()).end_time, '終了時刻は開始時刻より後にしてください。');
  fill({ start_time: '11:00', end_time: '11:00' });
  assert.equal(form.validate(formEl, today()).end_time, '終了時刻は開始時刻より後にしてください。');
});

test('検証: 過去日はエラー', () => {
  fill({ reserved_date: addDays(today(), -1) });
  assert.equal(form.validate(formEl, today()).reserved_date, '過去の日付には予約できません。');
});

test('検証: 会議室未選択はエラー、かつ収容人数の上限検証は行わない', () => {
  fill({ room_id: '', attendee_count: '9999' });
  const errors = form.validate(formEl, today());
  assert.equal(errors.room_id, '会議室を選択してください。');
  assert.equal(errors.attendee_count, null);
});

test('検証: 参加予定人数が収容人数+1 はエラー、ちょうどはOK', () => {
  fill({ room_id: 2, attendee_count: '5' });
  assert.equal(
    form.validate(formEl, today()).attendee_count,
    '参加予定人数が会議室の収容人数(4名)を超えています。'
  );
  fill({ room_id: 2, attendee_count: '4' });
  assert.equal(form.validate(formEl, today()).attendee_count, null);
});

test('会議室選択の変更時に収容人数が再検証される', () => {
  fill({ room_id: 1, attendee_count: '8' });
  const roomSelect = formEl.querySelector('[data-role="room_id"]');
  roomSelect.value = '2';
  roomSelect.dispatchEvent({ type: 'change', target: roomSelect });
  assert.equal(
    formEl.querySelector('[data-error-for="attendee_count"]').textContent,
    '参加予定人数が会議室の収容人数(4名)を超えています。'
  );
});

test('showConflict: 競合時間帯が重複エラー領域に出る', () => {
  form.showConflict(formEl, {
    message: '選択した時間帯はすでに予約されています。',
    extra: { conflicts: [{ reservation_id: 9, start_time: '10:00', end_time: '11:00' }] },
  });
  const text = formEl.querySelector('[data-role="conflict-error"]').textContent;
  assert.ok(text.includes('選択した時間帯はすでに予約されています。'));
  assert.ok(text.includes('10:00-11:00'));
});

test('showCapacityError: 収容人数超過領域に出る', () => {
  form.showCapacityError(formEl, { message: '参加予定人数が会議室の収容人数(4名)を超えています。' });
  assert.equal(
    formEl.querySelector('[data-role="capacity-error"]').textContent,
    '参加予定人数が会議室の収容人数(4名)を超えています。'
  );
});

// ※CR-001 オンライン会議URL(P002 3.3)
test('構成: オンライン会議URL欄が参加予定人数と備考の間にある', () => {
  const roles = formEl
    .querySelectorAll('[data-role]')
    .map((n) => n.getAttribute('data-role'));
  const url = roles.indexOf('meeting_url');
  assert.ok(url > 0);
  assert.ok(roles.indexOf('attendee_count') < url);
  assert.ok(url < roles.indexOf('note'));
  assert.equal(formEl.querySelector('[data-role="meeting_url"]').getAttribute('type'), 'text');
});

test('値の読み書き: オンライン会議URLが往復する', () => {
  fill({ meeting_url: 'https://example.com/meet/abc' });
  assert.equal(form.readValues(formEl).meeting_url, 'https://example.com/meet/abc');
  fill({ meeting_url: null });
  assert.equal(form.readValues(formEl).meeting_url, '');
});

test('toBody: オンライン会議URLが含まれ、空欄は空文字になる', () => {
  fill({ meeting_url: 'https://example.com/meet/abc' });
  assert.equal(form.toBody(formEl).meeting_url, 'https://example.com/meet/abc');
  fill({ meeting_url: '' });
  assert.equal(form.toBody(formEl).meeting_url, '');
});

test('検証: オンライン会議URLの空欄はOK、不正な値はエラー', () => {
  fill({ meeting_url: '' });
  assert.equal(form.validate(formEl, today()).meeting_url, null);
  fill({ meeting_url: 'example.com' });
  assert.equal(
    form.validate(formEl, today()).meeting_url,
    'オンライン会議URLは http:// または https:// で始まるURLを入力してください。'
  );
  fill({ meeting_url: 'https://' + 'a'.repeat(493) });
  assert.equal(
    form.validate(formEl, today()).meeting_url,
    'オンライン会議URLは500文字以内で入力してください。'
  );
});

test('検証: オンライン会議URLのエラーがフィールド直下に表示される', () => {
  fill({ meeting_url: 'ftp://example.com' });
  const errors = form.validate(formEl, today());
  form.showErrors(formEl, errors);
  assert.equal(
    formEl.querySelector('[data-error-for="meeting_url"]').textContent,
    'オンライン会議URLは http:// または https:// で始まるURLを入力してください。'
  );
});
