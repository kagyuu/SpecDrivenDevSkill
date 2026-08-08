// S05 マイ予約一覧画面(P002 3.5 / 4)。U004-T4。
// 並び順はAPIの返却順をそのままに使う(クライアント側で並べ替えない)。

import * as api from '../lib/api.js';
import { renderHeader } from '../components/header.js';
import { clear, el } from '../lib/dom.js';
import { navigate } from '../lib/router.js';

export const EMPTY_MESSAGE = '該当する予約はありません。';
export const COLUMNS = ['日付', '会議室名', '時間帯', '件名'];

const state = { me: null, period: 'upcoming', reservations: [] };

export function getState() {
  return state;
}

function reservationRow(reservation) {
  const row = el('tr', { 'data-reservation-id': String(reservation.reservation_id) }, [
    el('td', { 'data-column': 'reserved_date', text: reservation.reserved_date }),
    el('td', { 'data-column': 'room_name', text: reservation.room_name }),
    el('td', {
      'data-column': 'time_range',
      text: `${reservation.start_time}-${reservation.end_time}`,
    }),
    el('td', { 'data-column': 'title', text: reservation.title }),
  ]);
  // 行のクリックでS04へ(P002 3.5 / 4)
  row.addEventListener('click', () => navigate(`#/reservations/${reservation.reservation_id}`));
  return row;
}

function periodRadio(root, value, label) {
  const input = el('input', {
    type: 'radio', name: 'period', 'data-role': 'period', 'data-period': value,
    checked: state.period === value,
  });
  input.addEventListener('change', () => changePeriod(root, value));
  return el('label', { class: 'period-filter' }, [input, el('span', { text: label })]);
}

export function view(root) {
  clear(root);
  const container = el('div', { 'data-view': 's05-my-reservations' }, [
    el('h1', { text: 'マイ予約' }),
    el('div', { class: 'top-message', 'data-top-message': '' }),
  ]);
  root.appendChild(container);
  container.appendChild(
    el('div', { 'data-role': 'period-filters' }, [
      periodRadio(container, 'upcoming', '今後の予約'),
      periodRadio(container, 'past', '過去の予約'),
    ])
  );
  if (!state.reservations || state.reservations.length === 0) {
    container.appendChild(el('p', { 'data-role': 'empty-message', text: EMPTY_MESSAGE }));
    return container;
  }
  container.appendChild(
    el('table', { 'data-role': 'reservation-list' }, [
      el('thead', {}, [el('tr', {}, COLUMNS.map((t) => el('th', { text: t })))]),
      el('tbody', { 'data-role': 'reservation-rows' }, state.reservations.map(reservationRow)),
    ])
  );
  return container;
}

function rootOf(node) {
  if (node && node.getAttribute && node.getAttribute('data-view') === 's05-my-reservations') {
    return node.parentNode;
  }
  return node;
}

export async function changePeriod(root, period) {
  const target = rootOf(root);
  state.period = period;
  await fetchReservations();
  return view(target);
}

async function fetchReservations() {
  const payload = await api.get(`/api/reservations/mine?period=${state.period}`);
  state.reservations = payload.reservations || [];
}

export async function render(_params, root, headerRoot) {
  const target = root || document.getElementById('app');
  const header = headerRoot || document.getElementById('header');
  // 401 は api.js の共通処理でS01へ戻る(P002 2.3)
  state.me = (await api.get('/api/me')).user;
  if (header) renderHeader(header, state.me);
  state.period = 'upcoming'; // 初期値=今後の予約(P002 3.5)
  state.reservations = [];
  await fetchReservations();
  return view(target);
}
