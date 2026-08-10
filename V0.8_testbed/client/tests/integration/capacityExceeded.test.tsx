// P103 integration test T008 (docs/P008-test-direction/T008-capacity-exceeded-display.md).
// Confirms both client-side immediate validation AND the server-side
// validation (bypassing the client check via a direct fetch call, per this
// task's own 手順4) reject an attendee_count over the room's capacity.
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
})

after(async () => {
  await server.stop()
})

test('client-side validation shows the capacity error immediately', async () => {
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

  // 手順1・2
  fireEvent.change(screen.getByLabelText('会議室'), { target: { value: String(roomId) } })
  fireEvent.change(screen.getByLabelText('参加予定人数'), { target: { value: '9' } })
  fireEvent.change(screen.getByLabelText('日付'), { target: { value: '2099-01-01' } })
  fireEvent.change(screen.getByLabelText('開始時刻'), { target: { value: '10:00' } })
  fireEvent.change(screen.getByLabelText('終了時刻'), { target: { value: '11:00' } })
  fireEvent.change(screen.getByLabelText('件名'), { target: { value: '大人数会議' } })
  fireEvent.click(screen.getByRole('button', { name: '登録' }))

  // 手順3
  assert.ok(await screen.findByText('選択した会議室の収容人数(8名)を超えています'))
})

test('bypassing the client check, the server also rejects the over-capacity value with 400', async () => {
  // 手順4: クライアント側検証をバイパスし、APIを直接呼び出す。
  const response = await fetch('/api/reservations', {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      room_id: roomId,
      date: '2099-01-01',
      start_time: '10:00',
      end_time: '11:00',
      title: '大人数会議',
      participant_user_ids: [],
      attendee_count: 9,
      notes: null,
    }),
  })

  assert.equal(response.status, 400)
  const body = await response.json()
  assert.equal(body.error.code, 'VALIDATION_ERROR')
  assert.ok('attendee_count' in body.error.fields)
})
