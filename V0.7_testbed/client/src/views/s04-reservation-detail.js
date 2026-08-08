// S04 予約詳細・編集画面(P002 3.4 / 2.4 / 4)。U004-T3。
// 入力フォームはS03と同じ `reservation-form.js` を再利用する(別実装を作らない)。

import * as api from '../lib/api.js';
import { renderHeader } from '../components/header.js';
import { clear, el, setSubmitting, showApiError, showTopMessage } from '../lib/dom.js';
import { today as todayOf } from '../lib/datetime.js';
import * as form from '../components/reservation-form.js';
import { navigate } from '../lib/router.js';
import { setFlash } from './s02-calendar.js';

export const UPDATED_MESSAGE = '予約を更新しました。';
export const DELETED_MESSAGE = '予約を取り消しました。';
export const DELETE_CONFIRM_MESSAGE = 'この予約を取り消します。よろしいですか?';
export const PAST_RESERVATION_MESSAGE = '過去の予約は編集できません。';

let context = { me: null, reservation: null, rooms: [], candidates: [], origin: '#/calendar' };

export function getContext() {
  return context;
}

// 予約者本人または管理者のみ編集・取消できる(P002 3.4)
export function canEdit(me, reservation) {
  if (!me || !reservation) return false;
  return me.user_id === reservation.user_id || me.role === 'admin';
}

export function isPast(reservation) {
  return !!reservation && reservation.reserved_date < todayOf();
}

function row(label, value, role) {
  return el('div', { class: 'detail-row' }, [
    el('span', { class: 'detail-label', text: label }),
    el('span', { class: 'detail-value', 'data-field': role, text: value }),
  ]);
}

// ※CR-001 オンライン会議URLの行(P002 3.4)。
// 登録されていればクリック可能なリンク(別タブ)、未登録なら「-」のテキストにする。
// リンクは el() で組み立てる(innerHTML による文字列連結でHTMLを作らない)。
export function meetingUrlRow(meetingUrl) {
  const url = meetingUrl === null || meetingUrl === undefined ? '' : String(meetingUrl);
  const value = el('span', { class: 'detail-value', 'data-field': 'meeting_url' });
  if (url === '') {
    value.textContent = '-';
  } else {
    value.appendChild(
      el('a', {
        href: url, text: url, target: '_blank', rel: 'noopener noreferrer',
        'data-role': 'meeting-url-link',
      })
    );
  }
  return el('div', { class: 'detail-row' }, [
    el('span', { class: 'detail-label', text: 'オンライン会議URL' }),
    value,
  ]);
}

export function view(root) {
  clear(root);
  const reservation = context.reservation;
  const container = el('div', { 'data-view': 's04-reservation-detail' }, [
    el('h1', { text: '予約詳細' }),
    el('div', { class: 'top-message', 'data-top-message': '' }),
  ]);
  root.appendChild(container);
  if (!reservation) return container;

  container.appendChild(row('会議室', reservation.room_name, 'room_name'));
  container.appendChild(row('日付', reservation.reserved_date, 'reserved_date'));
  container.appendChild(
    row('時間帯', `${reservation.start_time}-${reservation.end_time}`, 'time_range')
  );
  container.appendChild(row('件名', reservation.title, 'title'));
  container.appendChild(
    row('参加者', (reservation.attendees || []).map((a) => a.name).join(', '), 'attendees')
  );
  // 参加予定人数の未入力は「-」(P002 3.4)
  container.appendChild(
    row(
      '参加予定人数',
      reservation.attendee_count === null || reservation.attendee_count === undefined
        ? '-'
        : String(reservation.attendee_count),
      'attendee_count'
    )
  );
  container.appendChild(meetingUrlRow(reservation.meeting_url)); // ※CR-001
  container.appendChild(row('備考', reservation.note || '', 'note'));
  container.appendChild(row('予約者', reservation.user_name, 'user_name'));
  container.appendChild(row('登録日時', reservation.created_at, 'created_at'));
  container.appendChild(row('更新日時', reservation.updated_at, 'updated_at'));

  if (isPast(reservation)) {
    // 過去日の予約は権限にかかわらず編集・取消不可(P002 3.4)
    container.appendChild(
      el('p', { 'data-role': 'past-message', text: PAST_RESERVATION_MESSAGE })
    );
  } else if (canEdit(context.me, reservation)) {
    container.appendChild(
      el('button', {
        type: 'button', 'data-action': 'edit', text: '編集',
        onClick: () => openEdit(container),
      })
    );
    container.appendChild(
      el('button', {
        type: 'button', 'data-action': 'delete', text: '取消',
        onClick: () => remove(container),
      })
    );
  }
  container.appendChild(
    el('button', {
      type: 'button', 'data-action': 'cancel', text: 'キャンセル',
      onClick: () => navigate(context.origin || '#/calendar'), // 遷移元へ戻る(P002 3.4)
    })
  );
  return container;
}

export function openEdit(root) {
  if (root.querySelector('[data-role="reservation-form"]')) {
    return root.querySelector('[data-role="reservation-form"]');
  }
  const formEl = form.buildForm({ rooms: context.rooms, candidates: context.candidates });
  const reservation = context.reservation;
  form.setValues(formEl, {
    room_id: reservation.room_id,
    reserved_date: reservation.reserved_date,
    start_time: reservation.start_time,
    end_time: reservation.end_time,
    title: reservation.title,
    attendee_user_ids: (reservation.attendees || []).map((a) => a.user_id),
    attendee_count: reservation.attendee_count,
    meeting_url: reservation.meeting_url, // ※CR-001
    note: reservation.note,
  });
  formEl.addEventListener('submit', (event) => {
    if (event && event.preventDefault) event.preventDefault();
    return submit(root);
  });
  root.appendChild(formEl);
  root.appendChild(
    el('button', { type: 'button', 'data-action': 'save', text: '更新',
      onClick: () => submit(root) })
  );
  return formEl;
}

export async function submit(root) {
  const formEl = root.querySelector('[data-role="reservation-form"]');
  form.clearFormErrors(formEl);
  showTopMessage(root, '');
  const errors = form.validate(formEl, todayOf());
  if (form.hasErrors(errors)) {
    form.showErrors(formEl, errors);
    return false;
  }
  const button = root.querySelector('[data-action="save"]');
  setSubmitting(button, true);
  try {
    await api.put(
      `/api/reservations/${context.reservation.reservation_id}`, form.toBody(formEl)
    );
    setFlash(UPDATED_MESSAGE);
    navigate('#/calendar');
    return true;
  } catch (error) {
    if (error.status === 409 && error.code === 'RESERVATION_CONFLICT') {
      form.showConflict(formEl, error);
    } else if (error.status === 400 && error.code === 'CAPACITY_EXCEEDED') {
      form.showCapacityError(formEl, error);
    } else if (error.status === 400 && error.code === 'VALIDATION_ERROR') {
      showApiError(formEl, error);
    } else {
      showApiError(root, error); // 403 / 404 / 409 CONSTRAINT_VIOLATION は共通規則(P002 2.4)
    }
    return false;
  } finally {
    setSubmitting(button, false);
  }
}

export async function remove(root) {
  if (!globalThis.confirm(DELETE_CONFIRM_MESSAGE)) return false;
  showTopMessage(root, '');
  try {
    await api.del(`/api/reservations/${context.reservation.reservation_id}`);
    setFlash(DELETED_MESSAGE);
    navigate('#/calendar');
    return true;
  } catch (error) {
    showApiError(root, error);
    return false;
  }
}

export async function render(params, root, headerRoot) {
  const target = root || document.getElementById('app');
  const header = headerRoot || document.getElementById('header');
  context.me = (await api.get('/api/me')).user;
  if (header) renderHeader(header, context.me);
  context.reservation = null;
  // ★FIXME★ 遷移元(S02/S05)の伝え方がP002 3.4に定義されていないため、クエリ `from` で受け取り、
  // 未指定なら `#/calendar` へ戻す規約とした(P007 5章「未解決事項」#16)
  context.origin = (params && params.from) || '#/calendar';
  try {
    context.reservation = (
      await api.get(`/api/reservations/${(params || {}).reservation_id}`)
    ).reservation;
  } catch (error) {
    const container = view(target);
    showApiError(container, error); // 404 は「対象のデータが見つかりません。〜」(P002 2.4)
    return container;
  }
  // 編集モードで使う候補は詳細表示時にまとめて取得する(P002 5.8: S04 も API-04 / API-08 を使う)
  context.rooms = (await api.get('/api/rooms')).rooms || [];
  context.candidates = (await api.get('/api/users?scope=attendee_candidates')).users || [];
  return view(target);
}
