// 共通ヘッダー(P002 2.2 / 2.3)。S01では描画しない。

import { el, clear } from '../lib/dom.js';
import * as api from '../lib/api.js';
import { navigate } from '../lib/router.js';

export function renderHeader(container, me) {
  clear(container);
  if (!me) return container;
  const links = [
    el('a', { href: '#/calendar', text: 'カレンダー' }),
    el('a', { href: '#/my-reservations', text: 'マイ予約' }),
  ];
  // 管理者にのみ管理メニューを描画する(P002 2.3)
  if (me.role === 'admin') {
    links.push(el('a', { href: '#/admin/rooms', text: '会議室管理' }));
    links.push(el('a', { href: '#/admin/users', text: 'ユーザー管理' }));
  }
  const logout = el('button', { type: 'button', 'data-action': 'logout', text: 'ログアウト' });
  logout.addEventListener('click', async () => {
    try {
      await api.post('/api/auth/logout');
    } catch (e) {
      /* ログアウト失敗時もS01へ戻す */
    }
    navigate('#/login');
  });
  container.appendChild(
    el('nav', {}, [el('span', { text: '会議室予約システム' }), ...links,
      el('span', { 'data-user-name': '', text: me.name }), logout])
  );
  return container;
}
