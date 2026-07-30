// フロントエンド土台。docs/02-frontend-spec.md 画面遷移図に対応する簡易ハッシュルーター。
import { api } from "./api.js";
import { renderLogin } from "./views/login.js";
import { renderCalendar } from "./views/calendar.js";
import { renderMyReservations } from "./views/my-reservations.js";
import { renderRoomsAdmin } from "./views/rooms-admin.js";
import { renderUsersAdmin } from "./views/users-admin.js";
import { renderReservationForm } from "./views/reservation-form.js";
import { renderReservationDetail } from "./views/reservation-detail.js";

const main = document.getElementById("app-main");
const nav = document.getElementById("app-nav");

export const state = { user: null };

function renderNav() {
  if (!state.user) {
    nav.innerHTML = "";
    return;
  }
  const links = [
    ['#/calendar', 'カレンダー'],
    ['#/my-reservations', 'マイ予約'],
  ];
  if (state.user.role === 'admin') {
    links.push(['#/rooms-admin', '会議室管理']);
    links.push(['#/users-admin', 'ユーザー管理']);
  }
  nav.innerHTML = links.map(([href, label]) => `<a href="${href}">${label}</a>`).join(' ')
    + ` <a href="#" id="logout-link">ログアウト</a>`;
  document.getElementById('logout-link').addEventListener('click', async (e) => {
    e.preventDefault();
    await api.logout();
    state.user = null;
    location.hash = '#/login';
  });
}

async function route() {
  const hash = location.hash || '#/login';
  const [path, param] = hash.replace('#/', '').split('/');

  if (!state.user && path !== 'login') {
    try {
      state.user = await api.me();
    } catch (e) {
      location.hash = '#/login';
      return;
    }
  }

  renderNav();

  switch (path) {
    case 'login':
      renderLogin(main, async (user) => {
        state.user = user;
        location.hash = '#/calendar';
      });
      break;
    case 'calendar':
      renderCalendar(main, state.user);
      break;
    case 'my-reservations':
      renderMyReservations(main);
      break;
    case 'rooms-admin':
      renderRoomsAdmin(main, state.user);
      break;
    case 'users-admin':
      renderUsersAdmin(main, state.user);
      break;
    case 'reservation-new':
      renderReservationForm(main, null);
      break;
    case 'reservation':
      renderReservationDetail(main, param, state.user);
      break;
    default:
      main.innerHTML = '<p>Not Found</p>';
  }
}

window.addEventListener('hashchange', route);
window.addEventListener('DOMContentLoaded', route);
