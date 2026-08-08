// S03 予約作成画面(P002 3.3 / 2.4 / 4)。U004-T2。

import * as api from '../lib/api.js';
import { renderHeader } from '../components/header.js';
import { clear, el, setSubmitting, showApiError, showTopMessage } from '../lib/dom.js';
import { addMinutes, today as todayOf } from '../lib/datetime.js';
import * as form from '../components/reservation-form.js';
import { navigate } from '../lib/router.js';
import { setFlash } from './s02-calendar.js';

export const CREATED_MESSAGE = '予約を登録しました。';

let context = { me: null, rooms: [], candidates: [] };

export function getContext() {
  return context;
}

export function view(root, params = {}) {
  clear(root);
  const container = el('div', { 'data-view': 's03-reservation-new' }, [
    el('h1', { text: '予約作成' }),
    el('div', { class: 'top-message', 'data-top-message': '' }),
  ]);
  root.appendChild(container);
  const formEl = form.buildForm(context);
  // S02の空きセルから引き継いだ値を初期値にする(P002 3.2 / 3.3)
  form.setValues(formEl, {
    room_id: params.room_id || '',
    reserved_date: params.date || todayOf(),
    start_time: params.start || '',
    end_time: params.end || (params.start ? addMinutes(params.start, 30) : ''),
    title: '',
    attendee_user_ids: [],
    attendee_count: '',
    note: '',
  });
  formEl.addEventListener('submit', (event) => {
    if (event && event.preventDefault) event.preventDefault();
    return submit(container);
  });
  container.appendChild(formEl);
  container.appendChild(
    el('button', { type: 'submit', 'data-action': 'save', text: '登録',
      onClick: () => submit(container) })
  );
  container.appendChild(
    el('button', {
      type: 'button', 'data-action': 'cancel', text: 'キャンセル',
      onClick: () => navigate('#/calendar'), // 確認なしでS02へ戻る(P002 3.3)
    })
  );
  return container;
}

export async function submit(root) {
  const formEl = root.querySelector('[data-role="reservation-form"]');
  form.clearFormErrors(formEl);
  showTopMessage(root, '');
  const errors = form.validate(formEl, todayOf());
  // クライアント側バリデーション違反ではAPIを呼ばない(P002 2.4)
  if (form.hasErrors(errors)) {
    form.showErrors(formEl, errors);
    return false;
  }
  const button = root.querySelector('[data-action="save"]');
  setSubmitting(button, true);
  try {
    await api.post('/api/reservations', form.toBody(formEl));
    setFlash(CREATED_MESSAGE);
    navigate('#/calendar');
    return true;
  } catch (error) {
    if (error.status === 409 && error.code === 'RESERVATION_CONFLICT') {
      form.showConflict(formEl, error);
    } else if (error.status === 400 && error.code === 'CAPACITY_EXCEEDED') {
      form.showCapacityError(formEl, error);
    } else {
      showApiError(formEl, error);
      if (!(error.status === 400 && error.code === 'VALIDATION_ERROR')) {
        showApiError(root, error);
      }
    }
    return false;
  } finally {
    setSubmitting(button, false);
  }
}

export async function render(params, root, headerRoot) {
  const target = root || document.getElementById('app');
  const header = headerRoot || document.getElementById('header');
  context.me = (await api.get('/api/me')).user;
  if (header) renderHeader(header, context.me);
  context.rooms = (await api.get('/api/rooms')).rooms || [];
  // 参加者候補は一般ユーザーでも取得できる(P002 5.6 API-08 `scope=attendee_candidates`)
  context.candidates = (await api.get('/api/users?scope=attendee_candidates')).users || [];
  return view(target, params || {});
}
