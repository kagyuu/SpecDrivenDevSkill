// S06 会議室管理画面(管理者用。P002 3.6 / 2.3 / 2.4)

import * as api from '../lib/api.js';
import { renderHeader } from '../components/header.js';
import { clear, el, showApiError, showFieldError, clearFieldErrors, showTopMessage, setSubmitting } from '../lib/dom.js';
import {
  validateCapacity, validateDescription, validateEquipment, validateRoomName,
} from '../lib/validation.js';

export const NO_PERMISSION_MESSAGE = 'この画面を表示する権限がありません。';
export const DELETE_CONFIRM_MESSAGE = 'この会議室を無効化します。よろしいですか?';

function field(labelText, name, type = 'text') {
  return el('div', { class: 'field' }, [
    el('label', { for: `room-${name}`, text: labelText }),
    el('input', { id: `room-${name}`, name, type }),
    el('div', { class: 'field-error', 'data-error-for': name }),
  ]);
}

function roomRow(room) {
  const row = el('tr', {
    'data-room-id': String(room.room_id),
    class: room.is_active ? '' : 'is-inactive',
  }, [
    el('td', { text: room.name }),
    el('td', { text: String(room.capacity) }),
    el('td', { text: room.equipment || '' }),
    el('td', { 'data-column': 'description', text: room.description || '' }),
    el('td', { text: room.is_active ? '有効' : '無効' }),
    el('td', {}, [
      el('button', { type: 'button', 'data-action': 'edit', 'data-room-id': String(room.room_id), text: '編集' }),
      el('button', { type: 'button', 'data-action': 'delete', 'data-room-id': String(room.room_id), text: '削除' }),
    ]),
  ]);
  return row;
}

export function view(root, me, rooms) {
  currentMe = me; // 再描画(reload)でも同じ権限で描き直せるように保持する
  clear(root);
  const container = el('div', { 'data-view': 's06-room-admin' }, [
    el('div', { class: 'top-message', 'data-top-message': '' }),
  ]);
  root.appendChild(container);
  // 権限による表示制御(P002 2.3。API側でも403を返す二重の防御)
  if (!me || me.role !== 'admin') {
    container.appendChild(el('p', { 'data-permission-message': '', text: NO_PERMISSION_MESSAGE }));
    container.appendChild(el('a', { href: '#/calendar', text: 'カレンダーへ戻る' }));
    return container;
  }
  container.appendChild(el('h1', { text: '会議室管理' }));
  container.appendChild(el('a', { href: '#/admin/users', 'data-link': 'users', text: 'ユーザー管理' }));
  container.appendChild(el('button', { type: 'button', 'data-action': 'new', text: '新規登録' }));
  container.appendChild(
    el('table', { 'data-role': 'room-list' }, [
      el('thead', {}, [
        el('tr', {}, ['会議室名', '収容人数', '設備', '説明文', '有効・無効', '操作'].map((t) => el('th', { text: t }))),
      ]),
      el('tbody', { 'data-role': 'room-rows' }, (rooms || []).map(roomRow)),
    ])
  );
  const form = el('form', { class: 'modal', 'data-role': 'room-form', 'data-duplicate-field': 'name' }, [
    el('input', { type: 'hidden', name: 'room_id' }),
    field('会議室名', 'name'),
    field('収容人数', 'capacity', 'number'),
    field('設備', 'equipment'),
    field('説明文', 'description'),
    el('div', { class: 'field' }, [
      el('label', { for: 'room-is_active', text: '有効' }),
      el('input', { id: 'room-is_active', name: 'is_active', type: 'checkbox', checked: true }),
    ]),
    el('button', { type: 'submit', 'data-action': 'save', text: '保存' }),
  ]);
  form.addEventListener('submit', (event) => {
    if (event && event.preventDefault) event.preventDefault();
    return submit(root);
  });
  container.appendChild(form);
  for (const button of container.querySelectorAll('[data-action="edit"]')) {
    button.addEventListener('click', () => openForm(root, findRoom(rooms, button.getAttribute('data-room-id'))));
  }
  for (const button of container.querySelectorAll('[data-action="delete"]')) {
    button.addEventListener('click', () => remove(root, button.getAttribute('data-room-id')));
  }
  container.querySelector('[data-action="new"]').addEventListener('click', () => openForm(root, null));
  return container;
}

function findRoom(rooms, roomId) {
  return (rooms || []).find((r) => String(r.room_id) === String(roomId)) || null;
}

export function openForm(root, room) {
  const form = root.querySelector('[data-role="room-form"]');
  clearFieldErrors(root);
  form.querySelector('[name="room_id"]').value = room ? String(room.room_id) : '';
  form.querySelector('[name="name"]').value = room ? room.name : '';
  form.querySelector('[name="capacity"]').value = room ? String(room.capacity) : '';
  form.querySelector('[name="equipment"]').value = room ? room.equipment || '' : '';
  form.querySelector('[name="description"]').value = room ? room.description || '' : '';
  form.querySelector('[name="is_active"]').checked = room ? !!room.is_active : true;
  return form;
}

function readForm(root) {
  const form = root.querySelector('[data-role="room-form"]');
  return {
    room_id: form.querySelector('[name="room_id"]').value,
    name: form.querySelector('[name="name"]').value,
    capacity: form.querySelector('[name="capacity"]').value,
    equipment: form.querySelector('[name="equipment"]').value,
    description: form.querySelector('[name="description"]').value,
    is_active: !!form.querySelector('[name="is_active"]').checked,
  };
}

export async function submit(root) {
  const input = readForm(root);
  clearFieldErrors(root);
  showTopMessage(root, '');
  const errors = {
    name: validateRoomName(input.name),
    capacity: validateCapacity(input.capacity),
    equipment: validateEquipment(input.equipment),
    description: validateDescription(input.description),
  };
  // クライアント側バリデーション違反ではAPIを呼ばない(P002 2.4)
  if (Object.values(errors).some(Boolean)) {
    for (const [field_, message] of Object.entries(errors)) showFieldError(root, field_, message);
    return false;
  }
  const body = {
    name: input.name,
    capacity: Number(input.capacity),
    equipment: input.equipment,
    description: input.description,
    is_active: input.is_active,
  };
  const button = root.querySelector('[data-action="save"]');
  setSubmitting(button, true);
  try {
    if (input.room_id) await api.put(`/api/rooms/${input.room_id}`, body);
    else await api.post('/api/rooms', body);
    await reload(root);
    return true;
  } catch (error) {
    showApiError(root, error);
    return false;
  } finally {
    setSubmitting(button, false);
  }
}

export async function remove(root, roomId) {
  if (!globalThis.confirm(DELETE_CONFIRM_MESSAGE)) return false;
  showTopMessage(root, '');
  try {
    await api.del(`/api/rooms/${roomId}`);
    await reload(root);
    return true;
  } catch (error) {
    showApiError(root, error); // 409 CONSTRAINT_VIOLATION は画面上部にAPIの message を表示
    return false;
  }
}

let currentMe = null;

export async function reload(root) {
  const rooms = (await api.get('/api/rooms?include_inactive=true')).rooms;
  return view(root, currentMe, rooms);
}

export async function render(_params, root, headerRoot) {
  const target = root || document.getElementById('app');
  const header = headerRoot || document.getElementById('header');
  currentMe = (await api.get('/api/me')).user;
  if (header) renderHeader(header, currentMe);
  if (currentMe.role !== 'admin') return view(target, currentMe, []);
  return reload(target);
}
