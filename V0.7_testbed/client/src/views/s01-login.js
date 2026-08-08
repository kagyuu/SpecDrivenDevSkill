// S01 ログイン画面(P002 3.1 / 2.4 / 4)。共通ヘッダーは描画しない。

import * as api from '../lib/api.js';
import { clear, el, showFieldError, clearFieldErrors, showTopMessage, setSubmitting } from '../lib/dom.js';
import { navigate } from '../lib/router.js';
import { validatePassword, validateUserId } from '../lib/validation.js';

export const AUTH_FAILED_MESSAGE = 'ユーザーIDまたはパスワードが正しくありません。';

function field(labelText, name, type) {
  return el('div', { class: 'field' }, [
    el('label', { for: name, text: labelText }),
    el('input', { id: name, name, type }),
    el('div', { class: 'field-error', 'data-error-for': name }),
  ]);
}

export function build() {
  const form = el('form', { 'data-view': 's01-login' }, [
    el('h1', { text: '会議室予約システム' }),
    el('div', { class: 'top-message', 'data-top-message': '' }),
    field('ユーザーID', 'user_id', 'text'),
    field('パスワード', 'password', 'password'),
    el('button', { type: 'submit', 'data-action': 'login', text: 'ログイン' }),
  ]);
  form.addEventListener('submit', (event) => {
    if (event && event.preventDefault) event.preventDefault();
    return submit(form);
  });
  return form;
}

export async function submit(root) {
  clearFieldErrors(root);
  showTopMessage(root, '');
  const userId = root.querySelector('[name="user_id"]').value;
  const password = root.querySelector('[name="password"]').value;
  const userIdError = validateUserId(userId);
  const passwordError = validatePassword(password);
  // クライアント側バリデーション違反ではAPIを呼ばない(P002 2.4)
  if (userIdError || passwordError) {
    showFieldError(root, 'user_id', userIdError);
    showFieldError(root, 'password', passwordError);
    return false;
  }
  const button = root.querySelector('[data-action="login"]');
  setSubmitting(button, true);
  try {
    await api.post('/api/auth/login', { user_id: userId, password });
    navigate('#/calendar');
    return true;
  } catch (error) {
    if (error.status === 401) showTopMessage(root, AUTH_FAILED_MESSAGE);
    else if (error.status === 400 && error.details && error.details.length > 0) {
      for (const detail of error.details) showFieldError(root, detail.field, detail.message);
    } else showTopMessage(root, error.message);
    return false;
  } finally {
    setSubmitting(button, false);
  }
}

export function render(_params, root, headerRoot) {
  const target = root || document.getElementById('app');
  const header = headerRoot || document.getElementById('header');
  if (header) clear(header); // S01では共通ヘッダーを描画しない(P002 2.2)
  clear(target);
  const form = build();
  target.appendChild(form);
  const pending = api.takePendingMessage();
  if (pending) showTopMessage(form, pending);
  return form;
}
