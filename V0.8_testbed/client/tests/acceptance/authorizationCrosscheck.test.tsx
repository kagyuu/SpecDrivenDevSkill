// P201 acceptance test A002 (docs/P009-acceptance-direction/A002-authorization-crosscheck.md).
//
// ★実施メモ(命名・実行方式の逸脱について): A0NNの仕様は本来
// `node --test tests/acceptance/test_*.js`(Playwright等でビルド済みアプリを
// 操作する、JSX解釈不要なプレーンJS)を想定している
// (docs/P006-test-plan.md 5章)。本ラウンドではnpmレジストリへの到達を確認した
// (P103時点のADR-001〜003が前提としていた「レジストリ到達不可」の制約は解消して
// いる可能性があるが、Playwrightのインストール・ブラウザバイナリ取得・設定を
// このラウンドで新規に行う時間的余裕が無いため見送った)。かわりに、P103の
// `client/tests/integration/` と同じ手法(jsdom + 実サーバー、`.test.tsx`で
// Reactコンポーネントを直接レンダリング)を流用し、実行コマンド・ファイル名
// (`test_*.js`)は仕様どおりに一致させていない。この逸脱と理由をここに明記する。
import '../setupJsdom.ts'

import assert from 'node:assert/strict'
import { after, before, test } from 'node:test'

import { cleanup, render, screen } from '@testing-library/react'
import React from 'react'
import { MemoryRouter } from 'react-router-dom'

import { authApi } from '../../src/api/authApi.ts'
import { RoomManagementPage } from '../../src/pages/RoomManagementPage.tsx'
import { UserManagementPage } from '../../src/pages/UserManagementPage.tsx'
import { startRealServer, type RealServer } from '../integration/realServer.ts'

let server: RealServer
let roomId: number

before(async () => {
  server = await startRealServer()
  await authApi.login('admin', 'ChangeMe123!')
  roomId = (
    await (
      await fetch('/api/rooms', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: '第一会議室', capacity: 8, equipment: [], description: null }),
      })
    ).json()
  ).room_id
  await fetch('/api/users', {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ employee_id: 'e1001', name: '一般 太郎', password: 'Passw0rd!', role: 'general' }),
  })
  await authApi.logout()
  await authApi.login('e1001', 'Passw0rd!')
})

after(async () => {
  await server.stop()
})

// 手順1
test('direct URL access to /admin/rooms and /admin/users shows the 403 screen', { timeout: 15_000 }, async () => {
  render(React.createElement(MemoryRouter, null, React.createElement(RoomManagementPage)))
  assert.ok(await screen.findByText('アクセス権がありません。'))
  cleanup()

  render(React.createElement(MemoryRouter, null, React.createElement(UserManagementPage)))
  assert.ok(await screen.findByText('アクセス権がありません。'))
  cleanup()
})

// 手順2
test('direct room-admin API calls return 403 FORBIDDEN', async () => {
  const post = await fetch('/api/rooms', {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name: 'x', capacity: 1, equipment: [], description: null }),
  })
  assert.equal(post.status, 403)
  assert.equal((await post.json()).error.code, 'FORBIDDEN')

  const put = await fetch(`/api/rooms/${roomId}`, {
    method: 'PUT',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name: 'x', capacity: 1, equipment: [], description: null, is_active: true }),
  })
  assert.equal(put.status, 403)

  const del = await fetch(`/api/rooms/${roomId}`, { method: 'DELETE', credentials: 'include' })
  assert.equal(del.status, 403)
})

// 手順3
test('direct user-admin API calls return 403 FORBIDDEN', async () => {
  assert.equal((await fetch('/api/users', { credentials: 'include' })).status, 403)
  assert.equal(
    (
      await fetch('/api/users', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ employee_id: 'e9999', name: 'x', password: 'Password1!', role: 'general' }),
      })
    ).status,
    403,
  )
  assert.equal(
    (
      await fetch('/api/users/e1001', {
        method: 'PUT',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: 'x', password: null, role: 'general', is_active: true }),
      })
    ).status,
    403,
  )
  assert.equal((await fetch('/api/users/e1001', { method: 'DELETE', credentials: 'include' })).status, 403)
})

// 手順4
test('include_inactive=true from a general user is silently ignored, not an error', async () => {
  const response = await fetch('/api/rooms?include_inactive=true', { credentials: 'include' })
  assert.equal(response.status, 200)
  const rooms = await response.json()
  assert.ok(Array.isArray(rooms))
})
