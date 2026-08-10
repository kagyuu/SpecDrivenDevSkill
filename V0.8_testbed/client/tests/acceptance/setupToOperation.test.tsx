// P201 acceptance test A010 (docs/P009-acceptance-direction/A010-acceptance-setup-to-operation.md).
// See authorizationCrosscheck.test.tsx for the naming/harness substitution note.
import '../setupJsdom.ts'

import assert from 'node:assert/strict'
import { after, before, test } from 'node:test'

import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import React from 'react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'

import { authApi } from '../../src/api/authApi.ts'
import { CalendarPage } from '../../src/pages/CalendarPage.tsx'
import { ReservationCreatePage } from '../../src/pages/ReservationCreatePage.tsx'
import { RoomManagementPage } from '../../src/pages/RoomManagementPage.tsx'
import { UserManagementPage } from '../../src/pages/UserManagementPage.tsx'
import { startRealServer, type RealServer } from '../integration/realServer.ts'

let server: RealServer

before(async () => {
  server = await startRealServer()
})

after(async () => {
  await server.stop()
})

test('operator sets up rooms and users, general users book, admin can see across all reservations', { timeout: 20_000 }, async () => {
  // 手順1: adminで会議室3件登録
  await authApi.login('admin', 'ChangeMe123!')
  render(React.createElement(MemoryRouter, null, React.createElement(RoomManagementPage)))
  await screen.findByRole('heading', { name: '会議室管理' })
  for (const name of ['小会議室A', '小会議室B', '大会議室']) {
    fireEvent.change(screen.getByLabelText('会議室名'), { target: { value: name } })
    fireEvent.change(screen.getByLabelText('収容人数'), { target: { value: '4' } })
    fireEvent.click(screen.getByRole('button', { name: '登録' }))
    await screen.findByText(name)
  }
  cleanup()

  // 手順2: 一般ユーザー3件登録
  render(React.createElement(MemoryRouter, null, React.createElement(UserManagementPage)))
  await screen.findByRole('heading', { name: 'ユーザー管理' })
  for (const [id, name] of [
    ['e1001', '一般 一郎'],
    ['e1002', '一般 二郎'],
    ['e1003', '一般 三郎'],
  ]) {
    fireEvent.change(screen.getByLabelText('社員ID'), { target: { value: id } })
    fireEvent.change(screen.getByLabelText('氏名'), { target: { value: name } })
    fireEvent.change(screen.getByLabelText('パスワード'), { target: { value: 'Password1!' } })
    fireEvent.click(screen.getByRole('button', { name: '登録' }))
    await screen.findByText(name)
  }
  cleanup()
  await authApi.logout()

  // 手順3: 一般ユーザーでログインし、3会議室すべてが選択肢・フィルタに表示される
  await authApi.login('e1001', 'Password1!')
  render(
    React.createElement(MemoryRouter, null, React.createElement(ReservationCreatePage)),
  )
  await screen.findByRole('option', { name: '小会議室A' })
  assert.ok(screen.getByRole('option', { name: '小会議室B' }))
  assert.ok(screen.getByRole('option', { name: '大会議室' }))
  cleanup()

  render(React.createElement(MemoryRouter, null, React.createElement(CalendarPage)))
  await screen.findByRole('heading', { name: '予約カレンダー' })
  // 会議室フィルタのチェックボックスは会議室一覧の非同期取得後にレンダリング
  // されるため、getByLabelText(同期・リトライ無し)ではなくfindByLabelTextを
  // 使って描画完了を待つ。
  assert.ok(await screen.findByLabelText('小会議室A'))
  assert.ok(screen.getByLabelText('小会議室B'))
  assert.ok(screen.getByLabelText('大会議室'))
  cleanup()

  // 手順4: 3会議室それぞれに1件ずつ予約
  const roomsResponse = await fetch('/api/rooms', { credentials: 'include' })
  const rooms = await roomsResponse.json()
  assert.equal(rooms.length, 3)
  for (const room of rooms) {
    const response = await fetch('/api/reservations', {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        room_id: room.room_id,
        date: '2099-01-01',
        start_time: '10:00',
        end_time: '11:00',
        title: `${room.name}の予約`,
        participant_user_ids: [],
        attendee_count: null,
        notes: null,
      }),
    })
    assert.equal(response.status, 201)
  }
  await authApi.logout()

  // 手順5: 別の一般ユーザーで自分に無関係な予約セルの見え方を確認
  await authApi.login('e1002', 'Password1!')
  const listResponse = await fetch(
    '/api/reservations?date_from=2099-01-01&date_to=2099-01-01',
    { credentials: 'include' },
  )
  const list = await listResponse.json()
  // docs/P002-frontend-spec.md 4.6節: 一覧には attendee_count/notes を含まない
  // (他者の予約であっても件名・予約者名までは見える設計)。
  assert.equal(list.length, 3)
  assert.ok(list.every((item: Record<string, unknown>) => !('attendee_count' in item)))
  await authApi.logout()

  // 手順6: adminで全予約を俯瞰できる(APIレベルで確認)
  await authApi.login('admin', 'ChangeMe123!')
  const adminListResponse = await fetch(
    '/api/reservations?date_from=2099-01-01&date_to=2099-01-01',
    { credentials: 'include' },
  )
  const adminList = await adminListResponse.json()
  assert.equal(adminList.length, 3)
})
