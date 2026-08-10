// P103 integration test T006 (docs/P008-test-direction/T006-reservation-create-success.md).
// Real ReservationCreatePage (S03) submission against a real server, then
// verifies both the SQLite row and the CalendarPage (S02) cell reflect it.
import '../setupJsdom.ts'

import assert from 'node:assert/strict'
import { after, before, test } from 'node:test'
import { DatabaseSync } from 'node:sqlite'

import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import React from 'react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'

import { authApi } from '../../src/api/authApi.ts'
import { CalendarPage } from '../../src/pages/CalendarPage.tsx'
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
  await fetch('/api/users', {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ employee_id: 'u001', name: '一般 太郎', password: 'Password1!', role: 'general' }),
  })
  await authApi.logout()
})

after(async () => {
  await server.stop()
})

test('creating a reservation via S03 saves it and S02 reflects it in the correct cell', async () => {
  await authApi.login('u001', 'Password1!')

  render(
    React.createElement(
      MemoryRouter,
      { initialEntries: [`/reservations/new?room_id=${roomId}&date=${TEST_DATE}&start_time=10:00`] },
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
  assert.equal((screen.getByLabelText('会議室') as HTMLSelectElement).value, String(roomId))
  assert.equal((screen.getByLabelText('日付') as HTMLInputElement).value, TEST_DATE)
  assert.equal((screen.getByLabelText('開始時刻') as HTMLInputElement).value, '10:00')

  fireEvent.change(screen.getByLabelText('終了時刻'), { target: { value: '11:00' } })
  fireEvent.change(screen.getByLabelText('件名'), { target: { value: '週次定例会議' } })
  fireEvent.change(screen.getByLabelText('参加予定人数'), { target: { value: '5' } })
  fireEvent.click(screen.getByRole('button', { name: '登録' }))

  // Success means no validation/conflict message appears and the form is
  // gone (component unmounts on navigate('/') - see ReservationCreatePage).
  await new Promise((resolve) => setTimeout(resolve, 300))
  assert.equal(screen.queryByRole('form', { name: '予約作成フォーム' }), null)
  cleanup()

  // 手順3
  const db = new DatabaseSync(server.dbPath, { readOnly: true })
  const row = db
    .prepare("SELECT title, attendee_count FROM reservations WHERE title = '週次定例会議'")
    .get() as { title: string; attendee_count: number } | undefined
  db.close()
  assert.ok(row, 'expected a reservations row for 週次定例会議')
  assert.equal(row?.attendee_count, 5)

  // 手順2: S02へ遷移後、該当セルを確認する。S02は既定で当日を表示するため、
  // 翌営業日の予約を見るには「次へ」を1回押す必要がある。
  render(
    React.createElement(MemoryRouter, null, React.createElement(CalendarPage)),
  )
  await screen.findByRole('heading', { name: '予約カレンダー' })
  fireEvent.click(screen.getByRole('button', { name: '次へ' }))

  const cells = await screen.findAllByRole('button', { name: /週次定例会議/ })
  assert.ok(cells.length > 0)
  assert.equal(document.body.textContent?.includes('5名'), false)
  cleanup()
})
