// U001-T5 単体テスト — validation.js(P002 3章の境界値)
import { test } from 'node:test';
import assert from 'node:assert/strict';
import * as v from '../src/lib/validation.js';

test('validateUserId: 境界値 4文字OK / 3文字NG / 20文字OK / 21文字NG', () => {
  assert.equal(v.validateUserId('abcd'), null);
  assert.equal(v.validateUserId('a'.repeat(20)), null);
  assert.equal(v.validateUserId('abc'), 'ユーザーIDは半角英数字4〜20文字で入力してください。');
  assert.equal(v.validateUserId('a'.repeat(21)), 'ユーザーIDは半角英数字4〜20文字で入力してください。');
  assert.equal(v.validateUserId('user_001'), 'ユーザーIDは半角英数字4〜20文字で入力してください。');
  assert.equal(v.validateUserId(''), 'ユーザーIDを入力してください。');
});

test('validatePassword: 8文字OK / 7文字NG / 64文字OK / 65文字NG', () => {
  assert.equal(v.validatePassword('a'.repeat(8)), null);
  assert.equal(v.validatePassword('a'.repeat(64)), null);
  assert.equal(v.validatePassword('a'.repeat(7)), 'パスワードは8〜64文字で入力してください。');
  assert.equal(v.validatePassword('a'.repeat(65)), 'パスワードは8〜64文字で入力してください。');
  assert.equal(v.validatePassword(''), 'パスワードを入力してください。');
  // 編集時の空欄は「変更しない」ため OK(P002 3.7)
  assert.equal(v.validateOptionalPassword(''), null);
  assert.equal(v.validateOptionalPassword('a'.repeat(7)), 'パスワードは8〜64文字で入力してください。');
});

test('validateTitle: 100文字OK / 101文字NG', () => {
  assert.equal(v.validateTitle('あ'.repeat(100)), null);
  assert.equal(v.validateTitle('あ'.repeat(101)), '件名は100文字以内で入力してください。');
  assert.equal(v.validateTitle(''), '件名を入力してください。');
});

test('validateNote: 500文字OK / 501文字NG', () => {
  assert.equal(v.validateNote('あ'.repeat(500)), null);
  assert.equal(v.validateNote('あ'.repeat(501)), '備考は500文字以内で入力してください。');
  assert.equal(v.validateNote(''), null);
});

test('validateTimeRange: 開始<終了OK / 同一NG', () => {
  assert.equal(v.validateTimeRange('09:00', '09:30'), null);
  assert.equal(v.validateTimeRange('09:00', '09:00'), '終了時刻は開始時刻より後にしてください。');
  assert.equal(v.validateTimeRange('10:00', '09:30'), '終了時刻は開始時刻より後にしてください。');
  assert.equal(v.validateTimeRange('', '09:30'), '開始時刻を選択してください。');
});

test('validateAttendeeCount: 収容人数と等しいときOK / +1でNG', () => {
  assert.equal(v.validateAttendeeCount(10, 10), null);
  assert.equal(v.validateAttendeeCount(11, 10), '参加予定人数が会議室の収容人数(10名)を超えています。');
  assert.equal(v.validateAttendeeCount(0, 10), '参加予定人数は1以上の整数で入力してください。');
  assert.equal(v.validateAttendeeCount(1.5, 10), '参加予定人数は1以上の整数で入力してください。');
  // 任意入力・会議室未選択時は上限検証を行わない(P002 3.3)
  assert.equal(v.validateAttendeeCount('', 10), null);
  assert.equal(v.validateAttendeeCount(9999, null), null);
});

test('validateRoomName / validateCapacity / validateEquipment / validateDescription', () => {
  assert.equal(v.validateRoomName('会議室A'), null);
  assert.equal(v.validateRoomName(''), '会議室名を入力してください。');
  assert.equal(v.validateCapacity(1), null);
  assert.equal(v.validateCapacity(500), null);
  assert.equal(v.validateCapacity(0), '収容人数は1以上500以下の整数で入力してください。');
  assert.equal(v.validateCapacity(501), '収容人数は1以上500以下の整数で入力してください。');
  assert.equal(v.validateCapacity(1.5), '収容人数は1以上500以下の整数で入力してください。');
  assert.equal(v.validateEquipment('あ'.repeat(200)), null);
  assert.equal(v.validateEquipment('あ'.repeat(201)), '設備は200文字以内で入力してください。');
  assert.equal(v.validateDescription('あ'.repeat(200)), null);
  assert.equal(v.validateDescription('あ'.repeat(201)), '説明文は200文字以内で入力してください。');
});

test('validateName / validateRole', () => {
  assert.equal(v.validateName('山田 太郎'), null);
  assert.equal(v.validateName('あ'.repeat(51)), '氏名は50文字以内で入力してください。');
  assert.equal(v.validateName(''), '氏名を入力してください。');
  assert.equal(v.validateRole('general'), null);
  assert.equal(v.validateRole('admin'), null);
  assert.equal(v.validateRole('owner'), '権限を選択してください。');
});

test('validateDate / validateAttendees', () => {
  assert.equal(v.validateDate('2026-08-10', '2026-08-05'), null);
  assert.equal(v.validateDate('2026-08-05', '2026-08-05'), null);
  assert.equal(v.validateDate('2026-08-04', '2026-08-05'), '過去の日付には予約できません。');
  assert.equal(v.validateDate('', '2026-08-05'), '日付を入力してください。');
  assert.equal(v.validateAttendees(new Array(50).fill('u')), null);
  assert.equal(v.validateAttendees(new Array(51).fill('u')), '参加者は50名以内で選択してください。');
});

// ※CR-001 オンライン会議URL(P002 3.3。任意・500文字以内・http(s):// 前方一致)
test('validateMeetingUrl: 空欄はエラーにしない', () => {
  assert.equal(v.validateMeetingUrl(''), null);
  assert.equal(v.validateMeetingUrl(null), null);
  assert.equal(v.validateMeetingUrl(undefined), null);
});

test('validateMeetingUrl: http:// と https:// は通る', () => {
  assert.equal(v.validateMeetingUrl('https://example.com/meet/abc'), null);
  assert.equal(v.validateMeetingUrl('http://example.com/meet/abc'), null);
  assert.equal(v.validateMeetingUrl('https://example.com:8443/a?b=c#d'), null);
});

test('validateMeetingUrl: 500文字は通り、501文字はエラー(境界値)', () => {
  const url500 = 'https://' + 'a'.repeat(492);
  assert.equal(url500.length, 500);
  assert.equal(v.validateMeetingUrl(url500), null);
  const url501 = 'https://' + 'a'.repeat(493);
  assert.equal(url501.length, 501);
  assert.equal(
    v.validateMeetingUrl(url501),
    'オンライン会議URLは500文字以内で入力してください。'
  );
});

test('validateMeetingUrl: スキームが無い/http(s)以外はエラー', () => {
  const message = 'オンライン会議URLは http:// または https:// で始まるURLを入力してください。';
  assert.equal(v.validateMeetingUrl('example.com/meet'), message);
  assert.equal(v.validateMeetingUrl('ftp://example.com/meet'), message);
  assert.equal(v.validateMeetingUrl('//example.com/meet'), message);
  assert.equal(v.validateMeetingUrl('HTTP://example.com'), message);
});

test('validateMeetingUrl: 文字数違反とスキーム違反の両方なら文字数のメッセージ(判定順序)', () => {
  assert.equal(
    v.validateMeetingUrl('ftp://' + 'a'.repeat(495)),
    'オンライン会議URLは500文字以内で入力してください。'
  );
});
