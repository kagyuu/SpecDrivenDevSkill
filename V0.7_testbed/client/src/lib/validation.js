// 入力バリデーション(P002 3章の各表と1対1)。
// 戻り値は null(OK)またはエラーメッセージ文字列。文言はP002の表と一字一句一致させる。

const USER_ID_PATTERN = /^[A-Za-z0-9]{4,20}$/;

function isBlank(value) {
  return value === null || value === undefined || String(value).trim() === '';
}

export function validateUserId(value) {
  if (isBlank(value)) return 'ユーザーIDを入力してください。';
  if (!USER_ID_PATTERN.test(String(value))) return 'ユーザーIDは半角英数字4〜20文字で入力してください。';
  return null;
}

export function validatePassword(value) {
  if (isBlank(value)) return 'パスワードを入力してください。';
  const length = String(value).length;
  if (length < 8 || length > 64) return 'パスワードは8〜64文字で入力してください。';
  return null;
}

// S07のパスワード欄(編集時は空欄なら変更しない。P002 3.7)
export function validateOptionalPassword(value) {
  if (isBlank(value)) return null;
  return validatePassword(value);
}

export function validateName(value) {
  if (isBlank(value)) return '氏名を入力してください。';
  if (String(value).length > 50) return '氏名は50文字以内で入力してください。';
  return null;
}

export function validateRole(value) {
  if (value !== 'general' && value !== 'admin') return '権限を選択してください。';
  return null;
}

export function validateTitle(value) {
  if (isBlank(value)) return '件名を入力してください。';
  if (String(value).length > 100) return '件名は100文字以内で入力してください。';
  return null;
}

export function validateNote(value) {
  if (value && String(value).length > 500) return '備考は500文字以内で入力してください。';
  return null;
}

export function validateRoomName(value) {
  if (isBlank(value)) return '会議室名を入力してください。';
  // ★FIXME★ 50文字超過時の文言はP002 3.6に記載がないため、他項目の言い回しに合わせた
  if (String(value).length > 50) return '会議室名は50文字以内で入力してください。';
  return null;
}

export function validateCapacity(value) {
  const num = Number(value);
  if (isBlank(value) || !Number.isInteger(num) || num < 1 || num > 500) {
    return '収容人数は1以上500以下の整数で入力してください。';
  }
  return null;
}

export function validateEquipment(value) {
  if (value && String(value).length > 200) return '設備は200文字以内で入力してください。';
  return null;
}

export function validateDescription(value) {
  if (value && String(value).length > 200) return '説明文は200文字以内で入力してください。';
  return null;
}

export function validateRoomSelection(value) {
  if (isBlank(value)) return '会議室を選択してください。';
  return null;
}

export function validateDate(value, today) {
  if (isBlank(value)) return '日付を入力してください。';
  if (today && String(value) < String(today)) return '過去の日付には予約できません。';
  return null;
}

export function validateTimeRange(start, end) {
  if (isBlank(start)) return '開始時刻を選択してください。';
  if (isBlank(end) || String(end) <= String(start)) return '終了時刻は開始時刻より後にしてください。';
  return null;
}

// 参加予定人数は任意入力。会議室未選択(capacity が null)のあいだは上限検証を行わない(P002 3.3)。
export function validateAttendeeCount(count, capacity) {
  if (isBlank(count)) return null;
  const num = Number(count);
  if (!Number.isInteger(num) || num < 1 || num > 9999) {
    return '参加予定人数は1以上の整数で入力してください。';
  }
  if (capacity !== null && capacity !== undefined && num > Number(capacity)) {
    return `参加予定人数が会議室の収容人数(${capacity}名)を超えています。`;
  }
  return null;
}

// ※CR-001 オンライン会議URL(P002 3.3)。任意入力。空欄はエラーとしない。
// 判定順序はP002 3.3の規定どおり「文字数 → スキーム」。両方に違反する場合は文字数のメッセージ。
// スキームは前方一致のみで判定し、URLの構文解析はしない(ADR-011)。
export const MEETING_URL_MAX_LENGTH = 500;
export function validateMeetingUrl(value) {
  if (value === null || value === undefined || String(value) === '') return null;
  const text = String(value);
  if (text.length > MEETING_URL_MAX_LENGTH) return 'オンライン会議URLは500文字以内で入力してください。';
  if (!text.startsWith('http://') && !text.startsWith('https://')) {
    return 'オンライン会議URLは http:// または https:// で始まるURLを入力してください。';
  }
  return null;
}

export function validateAttendees(userIds) {
  const list = userIds || [];
  if (list.length > 50) return '参加者は50名以内で選択してください。';
  return null;
}
