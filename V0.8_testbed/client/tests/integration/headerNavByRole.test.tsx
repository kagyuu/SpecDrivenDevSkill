// P103 integration test T015 (docs/P008-test-direction/T015-header-nav-by-role.md).
// Real Header (via CalendarPage/RoomManagementPage) against a real server,
// for both a general user and an admin, plus the 403 access-control check
// for direct URL access.
import '../setupJsdom.ts'

import assert from 'node:assert/strict'
import { after, before, test } from 'node:test'

import { cleanup, render, screen } from '@testing-library/react'
import React from 'react'
import { MemoryRouter } from 'react-router-dom'

import { authApi } from '../../src/api/authApi.ts'
import { CalendarPage } from '../../src/pages/CalendarPage.tsx'
import { RoomManagementPage } from '../../src/pages/RoomManagementPage.tsx'
import { UserManagementPage } from '../../src/pages/UserManagementPage.tsx'
import { startRealServer, type RealServer } from './realServer.ts'

let server: RealServer

before(async () => {
  server = await startRealServer()
  await authApi.login('admin', 'ChangeMe123!')
  await fetch('/api/users', {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ employee_id: 'e1001', name: '一般 花子', password: 'Passw0rd!', role: 'general' }),
  })
  await authApi.logout()
})

after(async () => {
  await server.stop()
})

// 手順1
test('a general user sees only マイ予約/ログアウト in the header', { timeout: 15_000 }, async () => {
  await authApi.login('e1001', 'Passw0rd!')
  render(React.createElement(MemoryRouter, null, React.createElement(CalendarPage)))
  await screen.findByText('一般 花子')

  assert.ok(screen.getByRole('link', { name: 'マイ予約' }))
  assert.ok(screen.getByRole('button', { name: 'ログアウト' }))
  assert.equal(screen.queryByRole('link', { name: '会議室管理' }), null)
  assert.equal(screen.queryByRole('link', { name: 'ユーザー管理' }), null)

  cleanup()
  await authApi.logout()
})

// 手順2
test('an admin on S02 sees 会議室管理 but not ユーザー管理', { timeout: 15_000 }, async () => {
  await authApi.login('admin', 'ChangeMe123!')
  render(React.createElement(MemoryRouter, null, React.createElement(CalendarPage)))
  await screen.findByText('システム管理者')

  assert.ok(screen.getByRole('link', { name: 'マイ予約' }))
  assert.ok(screen.getByRole('link', { name: '会議室管理' }))
  assert.equal(screen.queryByRole('link', { name: 'ユーザー管理' }), null)

  cleanup()
  await authApi.logout()
})

// 手順3
test('an admin on S06 also sees ユーザー管理', { timeout: 15_000 }, async () => {
  await authApi.login('admin', 'ChangeMe123!')
  render(React.createElement(MemoryRouter, null, React.createElement(RoomManagementPage)))
  // RoomManagementPage自身の認可チェック(見出しの表示)と、Headerコンポーネント
  // 自身のgetMe()は別々の非同期処理であるため、見出しの表示だけを待っても
  // Header側の描画完了は保証されない。Header自身が描画する管理者名を待つことで
  // Headerの状態確定を確認する(手順2と同じパターン)。
  await screen.findByText('システム管理者')
  await screen.findByRole('heading', { name: '会議室管理' })

  assert.ok(screen.getByRole('link', { name: '会議室管理' }))
  assert.ok(screen.getByRole('link', { name: 'ユーザー管理' }))

  cleanup()
  await authApi.logout()
})

// 手順4
test('a general user directly accessing /admin/rooms or /admin/users sees the 403 screen', { timeout: 15_000 }, async () => {
  await authApi.login('e1001', 'Passw0rd!')

  render(React.createElement(MemoryRouter, null, React.createElement(RoomManagementPage)))
  assert.ok(await screen.findByText('アクセス権がありません。'))
  cleanup()

  render(React.createElement(MemoryRouter, null, React.createElement(UserManagementPage)))
  assert.ok(await screen.findByText('アクセス権がありません。'))
  cleanup()

  await authApi.logout()
})
