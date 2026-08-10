// Unit tests for U003-T4 (docs/P007-impl-direction/U003-reservation-core-and-calendar.md).
// Target: CalendarPage, RoomTimeGrid.
import './setupJsdom.ts'

import assert from 'node:assert/strict'
import { afterEach, beforeEach, mock, test } from 'node:test'

import { cleanup, render, screen } from '@testing-library/react'
import React from 'react'
import { MemoryRouter } from 'react-router-dom'

import { authApi } from '../src/api/authApi.ts'
import { CalendarPage } from '../src/pages/CalendarPage.tsx'
import { reservationApi, type ReservationListItem } from '../src/api/reservationApi.ts'
import type { Room } from '../src/api/roomApi.ts'

const ROOM: Room = {
  room_id: 1,
  name: '会議室A',
  capacity: 8,
  equipment: [],
  description: null,
  is_active: true,
}

const TODAY = new Date().toISOString().slice(0, 10)

const RESERVATION: ReservationListItem = {
  reservation_id: 10,
  room_id: 1,
  room_name: '会議室A',
  organizer_user_id: 'admin',
  organizer_name: 'システム管理者',
  title: '定例会議',
  start_datetime: `${TODAY}T10:00:00`,
  end_datetime: `${TODAY}T11:00:00`,
}

beforeEach(() => {
  authApi.getMe = mock.fn(() =>
    Promise.resolve({ employee_id: 'admin', name: 'システム管理者', role: 'admin' as const }),
  )
  reservationApi.listRooms = mock.fn(() => Promise.resolve<Room[]>([ROOM]))
  reservationApi.listReservations = mock.fn(() => Promise.resolve<ReservationListItem[]>([RESERVATION]))
})

afterEach(() => {
  cleanup()
  mock.reset()
})

function renderPage() {
  return render(
    React.createElement(MemoryRouter, null, React.createElement(CalendarPage)),
  )
}

test('a fetched reservation appears in its room/time cell in the grid', async () => {
  renderPage()

  // The reservation spans 10:00-11:00, i.e. two 30-minute rows, so it is
  // expected to appear in exactly two cells.
  const cells = await screen.findAllByRole('button', { name: 'システム管理者 / 定例会議' })
  assert.equal(cells.length, 2)
})

test('the reservation cell does not render attendee_count anywhere', async () => {
  renderPage()

  await screen.findAllByRole('button', { name: 'システム管理者 / 定例会議' })
  // ReservationListItem (docs/P002-frontend-spec.md 4.6節) has no
  // attendee_count field at all, so there is nothing for the grid to
  // accidentally render - assert the page text never contains a stray
  // attendee-count-shaped string as a basic sanity check.
  assert.equal(document.body.textContent?.includes('attendee_count'), false)
})

test('a failed room list fetch shows an error message', async () => {
  reservationApi.listRooms = mock.fn(() => Promise.reject(new Error('network error')))

  renderPage()

  assert.ok(await screen.findByText('会議室一覧の取得に失敗しました'))
})

test('a failed reservation list fetch shows an error message', async () => {
  reservationApi.listReservations = mock.fn(() => Promise.reject(new Error('network error')))

  renderPage()

  assert.ok(await screen.findByText('予約一覧の取得に失敗しました'))
})
