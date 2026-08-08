// 予約入力フォーム(S03とS04の編集モードで共有する部品。P002 3.3 / 3.4)。U004-T2。
// 画面固有の送信処理は持たない。値の保持・終日チェック・クライアント側バリデーションのみを担う。

import { el, showFieldError, clearFieldErrors } from '../lib/dom.js';
import { timeOptions } from '../lib/datetime.js';
import {
  validateAttendeeCount, validateAttendees, validateDate, validateMeetingUrl, validateNote,
  validateRoomSelection, validateTimeRange, validateTitle,
} from '../lib/validation.js';

// 終日チェック時の自動入力値(P002 3.3。P001の指定どおり)
export const ALL_DAY_START = '09:00';
export const ALL_DAY_END = '18:00';

//: 開始時刻は 08:00〜19:30、終了時刻は 08:30〜20:00 の30分刻み(P002 3.3)
export const START_OPTIONS = timeOptions('08:00', '19:30');
export const END_OPTIONS = timeOptions('08:30', '20:00');

function labelled(labelText, name, control) {
  return el('div', { class: 'field' }, [
    el('label', { for: `reservation-${name}`, text: labelText }),
    control,
    el('div', { class: 'field-error', 'data-error-for': name }),
  ]);
}

function select(name, values, labels = null) {
  const options = values.map((value, index) =>
    el('option', { value: String(value), text: labels ? labels[index] : String(value) })
  );
  return el('select', { id: `reservation-${name}`, name, 'data-role': name }, options);
}

/**
 * フォームを組み立てる。
 * @param {{rooms: Array, candidates: Array}} context 会議室(有効なもの)と参加者候補
 */
export function buildForm(context) {
  const rooms = (context && context.rooms) || [];
  const candidates = (context && context.candidates) || [];

  const roomSelect = select(
    'room_id',
    ['', ...rooms.map((r) => r.room_id)],
    ['選択してください', ...rooms.map((r) => r.name)]
  );
  const dateInput = el('input', {
    type: 'date', id: 'reservation-reserved_date', name: 'reserved_date',
    'data-role': 'reserved_date',
  });
  const allDay = el('input', {
    type: 'checkbox', id: 'reservation-all_day', name: 'all_day', 'data-role': 'all_day',
  });
  const startSelect = select('start_time', START_OPTIONS);
  const endSelect = select('end_time', END_OPTIONS);
  const titleInput = el('input', {
    type: 'text', id: 'reservation-title', name: 'title', 'data-role': 'title',
  });
  const attendeeSelect = el(
    'select',
    {
      id: 'reservation-attendee_user_ids', name: 'attendee_user_ids',
      'data-role': 'attendee_user_ids', multiple: 'multiple',
    },
    candidates.map((user) => el('option', { value: user.user_id, text: user.name }))
  );
  const countInput = el('input', {
    type: 'number', id: 'reservation-attendee_count', name: 'attendee_count',
    'data-role': 'attendee_count',
  });
  // ※CR-001 オンライン会議URL(任意)。項目の並びはP002 3.3の項目表に従う
  const meetingUrlInput = el('input', {
    type: 'text', id: 'reservation-meeting_url', name: 'meeting_url',
    'data-role': 'meeting_url',
  });
  const noteInput = el('textarea', {
    id: 'reservation-note', name: 'note', 'data-role': 'note',
  });

  const form = el('form', { 'data-role': 'reservation-form' }, [
    // 重複・収容人数超過は専用のエラー表示領域に出す(P002 3.3)
    el('div', { class: 'form-error', 'data-role': 'conflict-error' }),
    el('div', { class: 'form-error', 'data-role': 'capacity-error' }),
    labelled('会議室', 'room_id', roomSelect),
    labelled('日付', 'reserved_date', dateInput),
    el('div', { class: 'field' }, [
      el('label', { for: 'reservation-all_day', text: '終日' }),
      allDay,
    ]),
    labelled('開始時刻', 'start_time', startSelect),
    labelled('終了時刻', 'end_time', endSelect),
    labelled('件名', 'title', titleInput),
    labelled('参加者', 'attendee_user_ids', attendeeSelect),
    labelled('参加予定人数', 'attendee_count', countInput),
    labelled('オンライン会議URL', 'meeting_url', meetingUrlInput), // ※CR-001
    labelled('備考', 'note', noteInput),
  ]);
  form.context = { rooms, candidates };

  // 終日チェック: 開始 09:00 / 終了 18:00 を自動入力する。
  // 自動入力後の手動変更でチェックは外れず、チェックを外しても時刻は元に戻さない(P002 3.3)。
  allDay.addEventListener('change', () => {
    if (allDay.checked) {
      startSelect.value = ALL_DAY_START;
      endSelect.value = ALL_DAY_END;
    }
  });
  // 会議室変更時に収容人数の検証をやり直す(P002 3.3「会議室選択の変更時と送信時」)
  roomSelect.addEventListener('change', () => validateCapacityOnly(form));
  return form;
}

export function selectedRoom(form) {
  const roomId = form.querySelector('[data-role="room_id"]').value;
  if (!roomId) return null;
  const rooms = (form.context && form.context.rooms) || [];
  return rooms.find((room) => String(room.room_id) === String(roomId)) || null;
}

export function setValues(form, values = {}) {
  const set = (role, value) => {
    const node = form.querySelector(`[data-role="${role}"]`);
    if (node) node.value = value === null || value === undefined ? '' : String(value);
  };
  set('room_id', values.room_id);
  set('reserved_date', values.reserved_date);
  set('start_time', values.start_time);
  set('end_time', values.end_time);
  set('title', values.title);
  set('attendee_count', values.attendee_count);
  // ※CR-001 未登録は空文字(null を入れない)
  set('meeting_url', values.meeting_url === undefined || values.meeting_url === null
    ? '' : values.meeting_url);
  set('note', values.note === undefined || values.note === null ? '' : values.note);
  const selectedIds = (values.attendee_user_ids || []).map(String);
  for (const option of form.querySelectorAll('[data-role="attendee_user_ids"] option')) {
    option.selected = selectedIds.includes(String(option.value));
  }
  return form;
}

export function readValues(form) {
  const value = (role) => {
    const node = form.querySelector(`[data-role="${role}"]`);
    return node ? node.value : '';
  };
  const attendees = form
    .querySelectorAll('[data-role="attendee_user_ids"] option')
    .filter((option) => option.selected)
    .map((option) => option.value);
  return {
    room_id: value('room_id'),
    reserved_date: value('reserved_date'),
    all_day: !!form.querySelector('[data-role="all_day"]').checked,
    start_time: value('start_time'),
    end_time: value('end_time'),
    title: value('title'),
    attendee_user_ids: attendees,
    attendee_count: value('attendee_count'),
    meeting_url: value('meeting_url'), // ※CR-001
    note: value('note'),
  };
}

export function validate(form, today) {
  const input = readValues(form);
  const room = selectedRoom(form);
  // validateTimeRange は開始未選択なら開始のメッセージ、それ以外は終了のメッセージを返す(P002 3.3)
  const rangeError = validateTimeRange(input.start_time, input.end_time);
  return {
    room_id: validateRoomSelection(input.room_id),
    reserved_date: validateDate(input.reserved_date, today),
    start_time: input.start_time ? null : rangeError,
    end_time: input.start_time ? rangeError : null,
    title: validateTitle(input.title),
    attendee_user_ids: validateAttendees(input.attendee_user_ids),
    attendee_count: validateAttendeeCount(input.attendee_count, room ? room.capacity : null),
    meeting_url: validateMeetingUrl(input.meeting_url), // ※CR-001
    note: validateNote(input.note),
  };
}

// 会議室選択の変更時だけ動く軽い検証(P002 3.3)。会議室未選択のあいだは上限検証を行わない。
export function validateCapacityOnly(form) {
  const input = readValues(form);
  const room = selectedRoom(form);
  const message = validateAttendeeCount(input.attendee_count, room ? room.capacity : null);
  showFieldError(form, 'attendee_count', message || '');
  return message;
}

export function showErrors(form, errors) {
  clearFieldErrors(form);
  for (const [field, message] of Object.entries(errors)) {
    if (message) showFieldError(form, field, message);
  }
}

export function hasErrors(errors) {
  return Object.values(errors).some(Boolean);
}

export function clearFormErrors(form) {
  clearFieldErrors(form);
  const conflict = form.querySelector('[data-role="conflict-error"]');
  if (conflict) conflict.textContent = '';
  const capacity = form.querySelector('[data-role="capacity-error"]');
  if (capacity) capacity.textContent = '';
}

// 409 RESERVATION_CONFLICT を重複エラー領域に表示する(P002 2.4 / 3.3)
export function showConflict(form, error) {
  const holder = form.querySelector('[data-role="conflict-error"]');
  if (!holder) return;
  const conflicts = (error && error.extra && error.extra.conflicts) || [];
  const slots = conflicts.map((c) => `${c.start_time}-${c.end_time}`).join(', ');
  const message = (error && error.message) || '選択した時間帯はすでに予約されています。';
  holder.textContent = slots ? `${message}(${slots})` : message;
}

// 400 CAPACITY_EXCEEDED を収容人数超過エラー領域に表示する(P002 2.4 / 3.3)
export function showCapacityError(form, error) {
  const holder = form.querySelector('[data-role="capacity-error"]');
  if (!holder) return;
  holder.textContent = (error && error.message) || '';
}

// APIへ送るボディ(P002 5.7 API-15/16。予約者は画面から指定しない)
export function toBody(form) {
  const input = readValues(form);
  return {
    room_id: Number(input.room_id),
    reserved_date: input.reserved_date,
    start_time: input.start_time,
    end_time: input.end_time,
    title: input.title,
    attendee_user_ids: input.attendee_user_ids,
    attendee_count: input.attendee_count === '' ? null : Number(input.attendee_count),
    meeting_url: input.meeting_url, // ※CR-001 空欄は '' のまま送る(null にしない。P002 5.3)
    note: input.note,
  };
}
