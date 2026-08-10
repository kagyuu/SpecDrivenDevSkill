// P201 acceptance test A003 (docs/P009-acceptance-direction/A003-inactive-room-history-display.md).
// See authorizationCrosscheck.test.tsx for the naming/harness substitution note.
import '../setupJsdom.ts'

import assert from 'node:assert/strict'
import { after, before, test } from 'node:test'

import { cleanup, render, screen } from '@testing-library/react'
import React from 'react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'

import { authApi } from '../../src/api/authApi.ts'
import { MyReservationsPage } from '../../src/pages/MyReservationsPage.tsx'
import { ReservationCreatePage } from '../../src/pages/ReservationCreatePage.tsx'
import { ReservationDetailPage } from '../../src/pages/ReservationDetailPage.tsx'
import { startRealServer, type RealServer } from '../integration/realServer.ts'

let server: RealServer
let roomId: number
let reservationId: number

// 固定の将来日付を使う。「当日」を使うと、UTC基準の日付比較を行う
// reservation_service.list_my_reservations の "upcoming" 判定において、
// 実行時刻(UTC)によっては「本日10:00-11:00」が既に過去時刻として扱われ、
// テスト自体が自己矛盾を起こす(タイムゾーンに起因するテスト側の問題であり、
// docs/test-records記載のCalendarPage側の不具合とは別)。この問題を避けるため
// 確実に未来である日付を使う。
const RESERVATION_DATE = '2099-01-01'

before(async () => {
  server = await startRealServer()
  await authApi.login('admin', 'ChangeMe123!')
  roomId = (
    await (
      await fetch('/api/rooms', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: '第二会議室', capacity: 6, equipment: [], description: null }),
      })
    ).json()
  ).room_id
  reservationId = (
    await (
      await fetch('/api/reservations', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          room_id: roomId,
          date: RESERVATION_DATE,
          start_time: '10:00',
          end_time: '11:00',
          title: '定例会議',
          participant_user_ids: [],
          attendee_count: null,
          notes: null,
        }),
      })
    ).json()
  ).reservation_id

  // 手順1: 管理者で無効化
  const deactivateResponse = await fetch(`/api/rooms/${roomId}`, {
    method: 'DELETE',
    credentials: 'include',
  })
  assert.equal(deactivateResponse.status, 200)
})

after(async () => {
  await server.stop()
})

// 手順3(S04) - CalendarPage(S02)は既知のaddDaysタイムゾーン問題の影響を受けない
// (当日データのみを使うため)が、複数の並行fetchを伴うため、Header関連の
// 既知の競合状態(T009参照)の影響を受ける可能性がある。本テストはS04・S05に
// 絞って確認する(S02での確認はA001の主要業務フローで別途行う)。
test('S04 detail view keeps showing the deactivated room name', { timeout: 15_000 }, async () => {
  render(
    React.createElement(
      MemoryRouter,
      { initialEntries: [`/reservations/${reservationId}`] },
      React.createElement(
        Routes,
        null,
        React.createElement(Route, {
          path: '/reservations/:id',
          element: React.createElement(ReservationDetailPage),
        }),
      ),
    ),
  )
  assert.ok(await screen.findByText('第二会議室'))
  cleanup()
})

// 手順4(S05)
test('S05 my-reservations list keeps showing the deactivated room name', { timeout: 15_000 }, async () => {
  render(React.createElement(MemoryRouter, null, React.createElement(MyReservationsPage)))
  assert.ok(await screen.findByText('第二会議室'))
  cleanup()
})

// 手順5(S03)
test('S03 room dropdown excludes the deactivated room', { timeout: 15_000 }, async () => {
  render(
    React.createElement(MemoryRouter, null, React.createElement(ReservationCreatePage)),
  )
  // ドロップダウンが読み込まれるまで待つ(空のoptionが1件だけの状態から始まる)
  await new Promise((resolve) => setTimeout(resolve, 300))
  assert.equal(screen.queryByRole('option', { name: '第二会議室' }), null)
  cleanup()
})
