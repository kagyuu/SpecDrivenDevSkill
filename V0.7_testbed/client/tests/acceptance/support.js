// 受け入れ結合テスト(P009)共通の下準備。
// 実サーバープロセス(uvicorn)を起動し、実APIで基準データセットを投入する。
// docs/P009-acceptance-direction.md 3章「開始時にDBファイルを作り直して基準データセットを投入する」

import assert from 'node:assert/strict';
import { startServer, makeFetch } from '../helpers/server.js';

export const PASSWORD = 'Passw0rd!23';

export const BASE_USERS = [
  { user_id: 'user001', name: '山田 太郎', role: 'general', password: PASSWORD },
  { user_id: 'user002', name: '鈴木 花子', role: 'general', password: PASSWORD },
  { user_id: 'user003', name: '退職 次郎', role: 'general', password: PASSWORD, is_active: false },
];

export const BASE_ROOMS = [
  { name: '会議室A', capacity: 10, equipment: 'プロジェクタ', description: '' },
  { name: '会議室B', capacity: 4 },
  { name: '会議室C', capacity: 20, is_active: false },
];

export function jsonCaller(httpFetch) {
  return async function callJson(path, method = 'GET', body) {
    const options = { method, headers: { 'Content-Type': 'application/json' } };
    if (body !== undefined) options.body = JSON.stringify(body);
    return httpFetch(path, options);
  };
}

// サーバーを起動し、基準データセット(P006 5章)を投入して room_id を返す。
export async function startWithBaseData({ rooms = BASE_ROOMS, users = BASE_USERS } = {}) {
  const server = await startServer();
  const httpFetch = makeFetch(server.baseUrl);
  const callJson = jsonCaller(httpFetch);
  const login = await callJson('/api/auth/login', 'POST', { user_id: 'admin001', password: PASSWORD });
  assert.equal(login.status, 200, '初期管理者でログインできること');
  for (const user of users) {
    const res = await callJson('/api/users', 'POST', user);
    assert.equal(res.status, 201, `ユーザー ${user.user_id} の投入`);
  }
  const roomIds = {};
  for (const room of rooms) {
    const res = await callJson('/api/rooms', 'POST', room);
    assert.equal(res.status, 201, `会議室 ${room.name} の投入`);
    roomIds[room.name] = (await res.json()).room.room_id;
  }
  return { server, httpFetch, callJson, roomIds };
}

// 独立したCookieを持つ「別のブラウザ」相当のクライアント。
export function newSession(server) {
  const httpFetch = makeFetch(server.baseUrl);
  return { httpFetch, callJson: jsonCaller(httpFetch) };
}
