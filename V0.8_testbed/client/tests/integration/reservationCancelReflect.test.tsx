// P103 integration test T011 (docs/P008-test-direction/T011-reservation-cancel-reflect.md).
// Real ReservationDetailPage cancel flow against a real server, then
// verifies both the SQLite row is gone and CalendarPage (S02) reflects the
// empty slot.
import '../setupJsdom.ts'

import assert from 'node:assert/strict'
import { after, before, test } from 'node:test'
import { DatabaseSync } from 'node:sqlite'

import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import React from 'react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'

import { authApi } from '../../src/api/authApi.ts'
import { CalendarPage } from '../../src/pages/CalendarPage.tsx'
import { ReservationDetailPage } from '../../src/pages/ReservationDetailPage.tsx'
import { startRealServer, type RealServer } from './realServer.ts'

let server: RealServer
let roomId: number
let reservationId: number

function todayIsoDate(): string {
  return new Date().toISOString().slice(0, 10)
}

const TEST_DATE = todayIsoDate()

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
  reservationId = (
    await (
      await fetch('/api/reservations', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          room_id: roomId,
          date: TEST_DATE,
          start_time: '10:00',
          end_time: '11:00',
          title: '週次定例会議',
          participant_user_ids: [],
          attendee_count: null,
          notes: null,
        }),
      })
    ).json()
  ).reservation_id
})

after(async () => {
  await server.stop()
})

test('cancelling a reservation via S04 deletes it and S02 shows an empty slot', async () => {
  const originalConfirm = window.confirm
  window.confirm = () => true

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

  await screen.findByRole('form', { name: '予約編集フォーム' })

  // 手順1
  fireEvent.click(screen.getByRole('button', { name: '取消' }))
  await new Promise((resolve) => setTimeout(resolve, 300))

  window.confirm = originalConfirm
  cleanup()

  // 手順3
  const db = new DatabaseSync(server.dbPath, { readOnly: true })
  const row = db
    .prepare('SELECT reservation_id FROM reservations WHERE reservation_id = ?')
    .get(reservationId)
  db.close()
  assert.equal(row, undefined)

  // 手順2
  render(React.createElement(MemoryRouter, null, React.createElement(CalendarPage)))
  await screen.findByRole('heading', { name: '予約カレンダー' })
  await new Promise((resolve) => setTimeout(resolve, 300))
  assert.equal(screen.queryByRole('button', { name: /週次定例会議/ }), null)
  cleanup()
})
