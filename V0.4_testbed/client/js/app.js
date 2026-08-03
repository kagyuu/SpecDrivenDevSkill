// アプリケーションのルーティング起点(簡易ハッシュルータ)。
import * as authApi from "./api/authApi.js";
import * as roomApi from "./api/roomApi.js";
import * as userApi from "./api/userApi.js";
import * as reservationApi from "./api/reservationApi.js";
import { mountLoginPage } from "./pages/loginPage.js";
import { mountRoomManagementPage } from "./pages/roomManagementPage.js";
import { mountUserManagementPage } from "./pages/userManagementPage.js";
import { mountCalendarPage } from "./pages/calendarPage.js";
import { mountReservationCreatePage } from "./pages/reservationCreatePage.js";
import { mountReservationDetailPage } from "./pages/reservationDetailPage.js";
import { mountMyReservationsPage } from "./pages/myReservationsPage.js";

const appRoot = typeof document !== "undefined" ? document.getElementById("app") : null;

let currentUser = null;

function renderNav(root) {
  const nav = document.createElement("div");
  nav.className = "nav";
  nav.innerHTML = `
    <a href="#/calendar">カレンダー</a>
    <a href="#/reservations/new">予約作成</a>
    <a href="#/my-reservations">マイ予約</a>
    ${currentUser && currentUser.role === "admin" ? `
      <a href="#/rooms">会議室管理</a>
      <a href="#/users">ユーザー管理</a>
    ` : ""}
    <button id="logout-btn">ログアウト</button>
  `;
  root.appendChild(nav);
  nav.querySelector("#logout-btn").addEventListener("click", async () => {
    await authApi.logout();
    currentUser = null;
    route();
  });
}

async function route() {
  if (!appRoot) return;
  appRoot.innerHTML = "";

  if (!currentUser) {
    try {
      currentUser = await authApi.getMe();
    } catch (e) {
      // 未ログイン
    }
  }

  if (!currentUser) {
    mountLoginPage(appRoot, authApi, (user) => {
      currentUser = user;
      window.location.hash = "#/calendar";
      route();
    });
    return;
  }

  renderNav(appRoot);
  const contentDiv = document.createElement("div");
  appRoot.appendChild(contentDiv);

  const hash = window.location.hash || "#/calendar";
  const detailMatch = hash.match(/^#\/reservations\/(\d+)$/);

  if (hash === "#/rooms" && currentUser.role === "admin") {
    mountRoomManagementPage(contentDiv, roomApi);
  } else if (hash === "#/users" && currentUser.role === "admin") {
    mountUserManagementPage(contentDiv, userApi);
  } else if (hash === "#/reservations/new") {
    mountReservationCreatePage(contentDiv, roomApi, userApi, reservationApi, () => {
      window.location.hash = "#/calendar";
      route();
    });
  } else if (hash === "#/my-reservations") {
    mountMyReservationsPage(contentDiv, reservationApi);
  } else if (detailMatch) {
    mountReservationDetailPage(contentDiv, reservationApi, currentUser, Number(detailMatch[1]), () => {
      window.location.hash = "#/calendar";
      route();
    });
  } else {
    mountCalendarPage(contentDiv, roomApi, reservationApi);
  }
}

export function mount(root = appRoot) {
  route();
}

if (typeof document !== "undefined") {
  window.addEventListener("hashchange", route);
  if (document.readyState !== "loading") {
    mount();
  } else {
    document.addEventListener("DOMContentLoaded", () => mount());
  }
}
