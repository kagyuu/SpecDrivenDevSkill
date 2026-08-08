// S02 予約カレンダー画面(P002 3.2 / 2.3 / 2.4 / 4)。U004-T1。
// 会議室を列、時間帯(30分刻み)を行とするグリッドを、選択週(月曜起点7日間)の日付ごとに描画する。

import * as api from '../lib/api.js';
import { renderHeader } from '../components/header.js';
import { clear, el, showApiError, showTopMessage } from '../lib/dom.js';
import { addDays, addMinutes, endOfWeek, startOfWeek, timeOptions, today as todayOf, weekDates } from '../lib/datetime.js';
import { buildOccupancy, cellLabel, filterRooms, reservationAt } from '../lib/grid.js';
import { navigate } from '../lib/router.js';

// 行(時間帯)。表示は 08:00〜20:00 で、予約を開始できる最後のスロットは 19:30(P002 3.2 / 3.3)
export const SLOTS = timeOptions('08:00', '19:30');
export const PAST_DATE_MESSAGE = '過去の日付には予約できません。';

const WEEKDAYS = ['日', '月', '火', '水', '木', '金', '土'];

// 画面の状態。フィルタ切替でAPIを呼び直さないため、取得済みデータをここに保持する(P002 3.2)。
const state = {
  me: null,
  date: null,
  rooms: [],
  reservations: [],
  selectedRoomIds: [],
};

export function getState() {
  return state;
}

// S03/S04 の完了メッセージ(「予約を登録しました。」など)をS02へ引き渡すための1回限りの受け渡し口。
// P002 3.3 / 3.4 の「成功時はS02へ戻り〜を表示」を、画面間で共有状態を持たずに実現する。
let flashMessage = null;

export function setFlash(message) {
  flashMessage = message;
}

export function takeFlash() {
  const message = flashMessage;
  flashMessage = null;
  return message;
}

export function resetState() {
  state.me = null;
  state.date = null;
  state.rooms = [];
  state.reservations = [];
  state.selectedRoomIds = [];
}

function weekdayLabel(date) {
  const [y, m, d] = String(date).split('-').map(Number);
  return WEEKDAYS[new Date(y, m - 1, d).getDay()];
}

// 1日分のグリッド(会議室=列 / 時間帯=行)
function dayGrid(root, date, rooms, occupancy) {
  const header = el('tr', {}, [
    el('th', { text: '時間' }),
    ...rooms.map((room) => el('th', { 'data-room-id': String(room.room_id), text: room.name })),
  ]);
  const rows = SLOTS.map((slot) => {
    const cells = rooms.map((room) => {
      const reservation = reservationAt(occupancy, date, room.room_id, slot);
      const classes = ['cell'];
      if (reservation) classes.push('is-reserved');
      if (reservation && state.me && reservation.user_id === state.me.user_id) {
        classes.push('is-mine'); // 自分の予約は別配色(P002 3.2)
      }
      const cell = el('td', {
        class: classes.join(' '),
        'data-cell': '',
        'data-date': date,
        'data-room-id': String(room.room_id),
        'data-slot': slot,
        text: cellLabel(reservation), // 参加予定人数は含めない(P002 3.2)
      });
      if (reservation) {
        cell.setAttribute('data-reservation-id', String(reservation.reservation_id));
      }
      cell.addEventListener('click', () => onCellClick(root, cell));
      return cell;
    });
    return el('tr', {}, [el('th', { class: 'slot', text: slot }), ...cells]);
  });
  return el('section', { 'data-role': 'day-grid', 'data-date': date }, [
    el('h2', { text: `${date}(${weekdayLabel(date)})` }),
    el('table', { class: 'calendar' }, [el('thead', {}, [header]), el('tbody', {}, rows)]),
  ]);
}

// セルのクリック(P002 3.2)
export function onCellClick(root, cell) {
  const date = cell.getAttribute('data-date');
  const reservationId = cell.getAttribute('data-reservation-id');
  if (reservationId) {
    // 予約済みセル → S04(自分の予約でなくても詳細は閲覧できる)
    navigate(`#/reservations/${reservationId}`);
    return true;
  }
  if (date < todayOf()) {
    // 過去日の空きセルはS03へ遷移しない(P002 3.2)
    showTopMessage(root, PAST_DATE_MESSAGE);
    return false;
  }
  const roomId = cell.getAttribute('data-room-id');
  const slot = cell.getAttribute('data-slot');
  // 終了時刻は開始+30分としてS03へ引き継ぐ(P002 3.2)
  navigate(
    `#/reservations/new?room_id=${roomId}&date=${date}&start=${slot}&end=${addMinutes(slot, 30)}`
  );
  return true;
}

function controls(root) {
  const dateInput = el('input', {
    type: 'date', 'data-role': 'date-input', name: 'date', value: state.date,
  });
  dateInput.addEventListener('change', () => changeDate(root, dateInput.value));
  return el('div', { class: 'calendar-controls' }, [
    el('button', {
      type: 'button', 'data-action': 'prev-week', text: '前週',
      onClick: () => changeDate(root, addDays(state.date, -7)),
    }),
    el('button', {
      type: 'button', 'data-action': 'next-week', text: '翌週',
      onClick: () => changeDate(root, addDays(state.date, 7)),
    }),
    el('button', {
      type: 'button', 'data-action': 'today', text: '今日',
      onClick: () => changeDate(root, todayOf()),
    }),
    dateInput,
  ]);
}

function roomFilter(root) {
  const boxes = state.rooms.map((room) => {
    const input = el('input', {
      type: 'checkbox',
      'data-role': 'room-filter',
      'data-room-id': String(room.room_id),
      checked: state.selectedRoomIds.map(String).includes(String(room.room_id)),
    });
    // フィルタはクライアント側で絞り込む(再取得しない。P002 3.2)
    input.addEventListener('change', () => toggleRoom(root, room.room_id, input.checked));
    return el('label', { class: 'room-filter' }, [input, el('span', { text: room.name })]);
  });
  return el('div', { 'data-role': 'room-filters' }, boxes);
}

export function toggleRoom(root, roomId, checked) {
  const selected = new Set(state.selectedRoomIds.map(String));
  if (checked) selected.add(String(roomId));
  else selected.delete(String(roomId));
  state.selectedRoomIds = [...selected];
  return view(rootOf(root));
}

function rootOf(node) {
  // view() は #app 相当のコンテナを受け取る。内側のコンテナを渡されても親に遡る。
  if (node && node.getAttribute && node.getAttribute('data-view') === 's02-calendar') {
    return node.parentNode;
  }
  return node;
}

// 表示週を変える。予約データのみ取り直す(会議室マスタは変わらないため再取得しない)。
export async function changeDate(root, date) {
  const target = rootOf(root);
  state.date = date;
  await fetchReservations();
  return view(target);
}

async function fetchReservations() {
  const from = startOfWeek(state.date);
  const to = endOfWeek(state.date);
  const payload = await api.get(`/api/reservations?date_from=${from}&date_to=${to}`);
  state.reservations = payload.reservations || [];
}

export function view(root) {
  clear(root);
  const container = el('div', { 'data-view': 's02-calendar' }, [
    el('h1', { text: '予約カレンダー' }),
    el('div', { class: 'top-message', 'data-top-message': '' }),
  ]);
  root.appendChild(container);
  container.appendChild(controls(container));
  container.appendChild(roomFilter(container));
  const rooms = filterRooms(state.rooms, state.selectedRoomIds);
  const occupancy = buildOccupancy(state.reservations, SLOTS);
  const grids = el('div', { 'data-role': 'grids' });
  for (const date of weekDates(state.date)) {
    grids.appendChild(dayGrid(container, date, rooms, occupancy));
  }
  container.appendChild(grids);
  return container;
}

export async function render(params, root, headerRoot) {
  const target = root || document.getElementById('app');
  const header = headerRoot || document.getElementById('header');
  // 401 は api.js の共通処理でS01へ戻る(P002 2.3)
  state.me = (await api.get('/api/me')).user;
  if (header) renderHeader(header, state.me);
  state.date = (params && params.date) || todayOf();
  state.selectedRoomIds = [];
  try {
    // 会議室(列見出し)と予約(グリッド本体)を各1回だけ取得する(P002 3.2)
    state.rooms = (await api.get('/api/rooms')).rooms || [];
    await fetchReservations();
  } catch (error) {
    const container = view(target);
    showApiError(container, error);
    return container;
  }
  const container = view(target);
  const flash = takeFlash();
  if (flash) showTopMessage(container, flash, false);
  return container;
}
