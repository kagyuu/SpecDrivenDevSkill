// S07 ユーザー管理画面(管理者用。P002 3.7 / 2.3 / 2.4)

import * as api from '../lib/api.js';
import { renderHeader } from '../components/header.js';
import { clear, el, showApiError, showFieldError, clearFieldErrors, showTopMessage, setSubmitting } from '../lib/dom.js';
import {
  validateName, validateOptionalPassword, validatePassword, validateRole, validateUserId,
} from '../lib/validation.js';

export const NO_PERMISSION_MESSAGE = 'この画面を表示する権限がありません。';
export const DELETE_CONFIRM_MESSAGE = 'このユーザーを無効化します。よろしいですか?';
const ROLE_LABEL = { general: '一般', admin: '管理者' };

function field(labelText, name, type = 'text') {
  return el('div', { class: 'field' }, [
    el('label', { for: `user-${name}`, text: labelText }),
    el('input', { id: `user-${name}`, name, type }),
    el('div', { class: 'field-error', 'data-error-for': name }),
  ]);
}

function userRow(user) {
  return el('tr', {
    'data-user-id': user.user_id,
    class: user.is_active ? '' : 'is-inactive',
  }, [
    el('td', { text: user.user_id }),
    el('td', { text: user.name }),
    el('td', { text: ROLE_LABEL[user.role] || user.role }),
    el('td', { text: user.is_active ? '有効' : '無効' }),
    el('td', {}, [
      el('button', { type: 'button', 'data-action': 'edit', 'data-user-id': user.user_id, text: '編集' }),
      el('button', { type: 'button', 'data-action': 'delete', 'data-user-id': user.user_id, text: '削除' }),
    ]),
  ]);
}

export function view(root, me, users) {
  currentMe = me; // 再描画(reload)でも同じ権限で描き直せるように保持する
  clear(root);
  const container = el('div', { 'data-view': 's07-user-admin' }, [
    el('div', { class: 'top-message', 'data-top-message': '' }),
  ]);
  root.appendChild(container);
  if (!me || me.role !== 'admin') {
    container.appendChild(el('p', { 'data-permission-message': '', text: NO_PERMISSION_MESSAGE }));
    container.appendChild(el('a', { href: '#/calendar', text: 'カレンダーへ戻る' }));
    return container;
  }
  container.appendChild(el('h1', { text: 'ユーザー管理' }));
  container.appendChild(el('a', { href: '#/admin/rooms', 'data-link': 'back', text: '戻る' }));
  container.appendChild(el('button', { type: 'button', 'data-action': 'new', text: '新規登録' }));
  container.appendChild(
    el('table', { 'data-role': 'user-list' }, [
      el('thead', {}, [
        el('tr', {}, ['社員ID', '氏名', '権限', '有効・無効', '操作'].map((t) => el('th', { text: t }))),
      ]),
      el('tbody', { 'data-role': 'user-rows' }, (users || []).map(userRow)),
    ])
  );
  const roleSelect = el('select', { id: 'user-role', name: 'role' }, [
    el('option', { value: 'general', text: '一般' }),
    el('option', { value: 'admin', text: '管理者' }),
  ]);
  roleSelect.value = 'general';
  const form = el('form', { class: 'modal', 'data-role': 'user-form', 'data-duplicate-field': 'user_id' }, [
    el('input', { type: 'hidden', name: 'mode', value: 'create' }),
    field('社員ID', 'user_id'),
    field('氏名', 'name'),
    el('div', { class: 'field' }, [
      el('label', { for: 'user-role', text: '権限' }),
      roleSelect,
      el('div', { class: 'field-error', 'data-error-for': 'role' }),
    ]),
    el('div', { class: 'field' }, [
      el('label', { for: 'user-password', 'data-role': 'password-label', text: 'パスワード' }),
      el('input', { id: 'user-password', name: 'password', type: 'password' }),
      el('div', { class: 'field-error', 'data-error-for': 'password' }),
    ]),
    el('div', { class: 'field' }, [
      el('label', { for: 'user-is_active', text: '有効' }),
      el('input', { id: 'user-is_active', name: 'is_active', type: 'checkbox', checked: true }),
    ]),
    el('button', { type: 'submit', 'data-action': 'save', text: '保存' }),
  ]);
  form.addEventListener('submit', (event) => {
    if (event && event.preventDefault) event.preventDefault();
    return submit(root);
  });
  container.appendChild(form);
  for (const button of container.querySelectorAll('[data-action="edit"]')) {
    button.addEventListener('click', () =>
      openForm(root, findUser(users, button.getAttribute('data-user-id'))));
  }
  for (const button of container.querySelectorAll('[data-action="delete"]')) {
    button.addEventListener('click', () => remove(root, button.getAttribute('data-user-id')));
  }
  container.querySelector('[data-action="new"]').addEventListener('click', () => openForm(root, null));
  return container;
}

function findUser(users, userId) {
  return (users || []).find((u) => u.user_id === userId) || null;
}

export function openForm(root, user) {
  const form = root.querySelector('[data-role="user-form"]');
  clearFieldErrors(root);
  form.querySelector('[name="mode"]').value = user ? 'edit' : 'create';
  const userIdInput = form.querySelector('[name="user_id"]');
  userIdInput.value = user ? user.user_id : '';
  // 編集時、社員IDは表示のみ(P002 3.7)
  userIdInput.disabled = !!user;
  form.querySelector('[name="name"]').value = user ? user.name : '';
  form.querySelector('[name="role"]').value = user ? user.role : 'general';
  form.querySelector('[name="password"]').value = '';
  form.querySelector('[name="is_active"]').checked = user ? !!user.is_active : true;
  form.querySelector('[data-role="password-label"]').textContent = user
    ? 'パスワード(空欄なら変更しない)'
    : 'パスワード';
  return form;
}

function readForm(root) {
  const form = root.querySelector('[data-role="user-form"]');
  return {
    mode: form.querySelector('[name="mode"]').value,
    user_id: form.querySelector('[name="user_id"]').value,
    name: form.querySelector('[name="name"]').value,
    role: form.querySelector('[name="role"]').value,
    password: form.querySelector('[name="password"]').value,
    is_active: !!form.querySelector('[name="is_active"]').checked,
  };
}

export async function submit(root) {
  const input = readForm(root);
  const isEdit = input.mode === 'edit';
  clearFieldErrors(root);
  showTopMessage(root, '');
  const errors = {
    user_id: isEdit ? null : validateUserId(input.user_id),
    name: validateName(input.name),
    role: validateRole(input.role),
    password: isEdit ? validateOptionalPassword(input.password) : validatePassword(input.password),
  };
  if (Object.values(errors).some(Boolean)) {
    for (const [field_, message] of Object.entries(errors)) showFieldError(root, field_, message);
    return false;
  }
  const body = { name: input.name, role: input.role, is_active: input.is_active };
  // 編集時にパスワードが空欄なら `password` キー自体を送らない(P002 3.7)
  if (input.password) body.password = input.password;
  if (!isEdit) body.user_id = input.user_id;
  const button = root.querySelector('[data-action="save"]');
  setSubmitting(button, true);
  try {
    if (isEdit) await api.put(`/api/users/${input.user_id}`, body);
    else await api.post('/api/users', body);
    await reload(root);
    return true;
  } catch (error) {
    showApiError(root, error);
    return false;
  } finally {
    setSubmitting(button, false);
  }
}

export async function remove(root, userId) {
  if (!globalThis.confirm(DELETE_CONFIRM_MESSAGE)) return false;
  showTopMessage(root, '');
  try {
    await api.del(`/api/users/${userId}`);
    await reload(root);
    return true;
  } catch (error) {
    showApiError(root, error); // 409 CONSTRAINT_VIOLATION は画面上部にAPIの message を表示
    return false;
  }
}

let currentMe = null;

export async function reload(root) {
  const users = (await api.get('/api/users?include_inactive=true')).users;
  return view(root, currentMe, users);
}

export async function render(_params, root, headerRoot) {
  const target = root || document.getElementById('app');
  const header = headerRoot || document.getElementById('header');
  currentMe = (await api.get('/api/me')).user;
  if (header) renderHeader(header, currentMe);
  if (currentMe.role !== 'admin') return view(target, currentMe, []);
  return reload(target);
}
