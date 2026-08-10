// P103 integration test T007 (docs/P008-test-direction/T007-reservation-conflict-display.md).
// Real ReservationCreatePage against a real server: attempts to double-book
// an already-reserved slot and checks the 409 conflict message + input
// retention.
import '../setupJsdom.ts'

import assert from 'node:assert/strict'
import { after, before, test } from 'node:test'

import { fireEvent, render, screen } from '@testing-library/react'
import React from 'react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'

import { authApi } from '../../src/api/authApi.ts'
import { ReservationCreatePage } from '../../src/pages/ReservationCreatePage.tsx'
import { startRealServer, type RealServer } from './realServer.ts'

let server: RealServer
let roomId: number

function tomorrowIsoDate(): string {
  const date = new Date()
  date.setDate(date.getDate() + 1)
  return date.toISOString().slice(0, 10)
}

const TEST_DATE = tomorrowIsoDate()

before(async () => {
  server = await startRealServer()

  await authApi.login('admin', 'ChangeMe123!')
  const roomResponse = await fetch('/api/rooms', {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name: '第一会議室', capacity: 8, equipment: [], description: null }),
  })
  roomId = (await roomResponse.json()).room_id
  // T006の予約(第一会議室、翌営業日10:00-11:00、週次定例会議)を直接APIで用意する。
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
})

after(async () => {
  await server.stop()
})

test('booking an overlapping slot shows the conflict message and keeps the entered values', async () => {
  render(
    React.createElement(
      MemoryRouter,
      { initialEntries: ['/reservations/new'] },
      React.createElement(
        Routes,
        null,
        React.createElement(Route, {
          path: '/reservations/new',
          element: React.createElement(ReservationCreatePage),
        }),
      ),
    ),
  )

  await screen.findByRole('option', { name: '第一会議室' })

  // 手順1
  fireEvent.change(screen.getByLabelText('会議室'), { target: { value: String(roomId) } })
  fireEvent.change(screen.getByLabelText('日付'), { target: { value: TEST_DATE } })
  fireEvent.change(screen.getByLabelText('開始時刻'), { target: { value: '10:30' } })
  fireEvent.change(screen.getByLabelText('終了時刻'), { target: { value: '11:30' } })
  fireEvent.change(screen.getByLabelText('件名'), { target: { value: '臨時会議' } })
  fireEvent.click(screen.getByRole('button', { name: '登録' }))

  // 手順2
  assert.ok(await screen.findByText('選択した会議室・時間帯は既に予約されています'))

  // 手順3
  assert.equal((screen.getByLabelText('会議室') as HTMLSelectElement).value, String(roomId))
  assert.equal((screen.getByLabelText('日付') as HTMLInputElement).value, TEST_DATE)
  assert.equal((screen.getByLabelText('開始時刻') as HTMLInputElement).value, '10:30')
  assert.equal((screen.getByLabelText('終了時刻') as HTMLInputElement).value, '11:30')
  assert.equal((screen.getByLabelText('件名') as HTMLInputElement).value, '臨時会議')
})
