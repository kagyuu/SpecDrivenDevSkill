// Unit tests for U004-T3 (docs/P007-impl-direction/U004-reservation-detail-and-mylist.md).
// Target: ReservationDetailPage.
import './setupJsdom.ts'

import assert from 'node:assert/strict'
import { afterEach, beforeEach, mock, test } from 'node:test'

import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import React from 'react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'

import {
  ReservationApiError,
  reservationApi,
  type ParticipantCandidate,
  type ReservationDetail,
} from '../src/api/reservationApi.ts'
import { ReservationDetailPage } from '../src/pages/ReservationDetailPage.tsx'
import type { Room } from '../src/api/roomApi.ts'

const ROOM: Room = {
  room_id: 1,
  name: '会議室A',
  capacity: 8,
  equipment: [],
  description: null,
  is_active: true,
}

const EDITABLE_RESERVATION: ReservationDetail = {
  reservation_id: 1,
  room_id: 1,
  room_name: '会議室A',
  organizer_user_id: 'admin',
  organizer_name: 'システム管理者',
  date: '2099-01-01',
  start_time: '10:00',
  end_time: '11:00',
  title: '定例会議',
  participants: [],
  attendee_count: null,
  notes: null,
  meeting_url: null,
  editable: true,
}

beforeEach(() => {
  reservationApi.getReservation = mock.fn(() => Promise.resolve(EDITABLE_RESERVATION))
  reservationApi.listRooms = mock.fn(() => Promise.resolve<Room[]>([ROOM]))
  reservationApi.listParticipantCandidates = mock.fn(() =>
    Promise.resolve<ParticipantCandidate[]>([]),
  )
  reservationApi.updateReservation = mock.fn()
  reservationApi.cancelReservation = mock.fn(() => Promise.resolve())
})

afterEach(() => {
  cleanup()
  mock.reset()
})

function renderPage() {
  return render(
    React.createElement(
      MemoryRouter,
      { initialEntries: ['/reservations/1'] },
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
}

test('an editable reservation shows the edit form and a successful update navigates away', async () => {
  const updateMock = mock.fn(() => Promise.resolve({ ...EDITABLE_RESERVATION, title: '更新後' }))
  reservationApi.updateReservation = updateMock

  renderPage()
  await screen.findByRole('form', { name: '予約編集フォーム' })

  fireEvent.change(screen.getByLabelText('件名'), { target: { value: '更新後' } })
  fireEvent.click(screen.getByRole('button', { name: '更新' }))

  await waitFor(() => assert.equal(updateMock.mock.calls.length, 1));
  assert.equal(updateMock.mock.calls[0].arguments[0], 1)
})

test('clicking cancel-reservation and confirming calls cancelReservation', async () => {
  const originalConfirm = window.confirm
  window.confirm = () => true
  const cancelMock = mock.fn(() => Promise.resolve())
  reservationApi.cancelReservation = cancelMock

  renderPage()
  await screen.findByRole('form', { name: '予約編集フォーム' })

  fireEvent.click(screen.getByRole('button', { name: '取消' }))

  await waitFor(() => assert.equal(cancelMock.mock.calls.length, 1))
  window.confirm = originalConfirm
})

test('a non-organizer, non-admin user sees a read-only view instead of the edit form', async () => {
  reservationApi.getReservation = mock.fn(() =>
    Promise.resolve({ ...EDITABLE_RESERVATION, editable: false }),
  )

  renderPage()

  assert.ok(await screen.findByText('予約詳細'))
  assert.equal(screen.queryByRole('form', { name: '予約編集フォーム' }), null)
  assert.ok(screen.getByText('会議室A'))
})

test('submitting an invalid update shows a validation error', async () => {
  renderPage()
  await screen.findByRole('form', { name: '予約編集フォーム' })

  fireEvent.change(screen.getByLabelText('件名'), { target: { value: '' } })
  fireEvent.click(screen.getByRole('button', { name: '更新' }))

  assert.ok(await screen.findByText('件名を入力してください'))
})

test('a 409 response while updating shows the conflict message', async () => {
  reservationApi.updateReservation = mock.fn(() =>
    Promise.reject(
      new ReservationApiError(409, {
        code: 'RESERVATION_CONFLICT',
        message: '選択した会議室・時間帯は既に予約されています',
      }),
    ),
  )

  renderPage()
  await screen.findByRole('form', { name: '予約編集フォーム' })
  fireEvent.click(screen.getByRole('button', { name: '更新' }))

  assert.ok(await screen.findByText('選択した会議室・時間帯は既に予約されています'))
})

// CR-001 (docs/P901-cr-direction/CR-001.md, U004-T7) additions ------------

test('a non-organizer, non-admin user sees the meeting url as a clickable link when set', async () => {
  reservationApi.getReservation = mock.fn(() =>
    Promise.resolve({
      ...EDITABLE_RESERVATION,
      editable: false,
      meeting_url: 'https://example.com/meeting/123',
    }),
  )

  renderPage()

  const link = (await screen.findByText('https://example.com/meeting/123')) as HTMLAnchorElement
  assert.equal(link.tagName, 'A')
  assert.equal(link.getAttribute('href'), 'https://example.com/meeting/123')
  assert.equal(link.getAttribute('target'), '_blank')
})

test('a non-organizer, non-admin user sees "(未設定)" when the meeting url is not set', async () => {
  reservationApi.getReservation = mock.fn(() =>
    Promise.resolve({ ...EDITABLE_RESERVATION, editable: false, meeting_url: null }),
  )

  renderPage()

  assert.ok(await screen.findByText('(未設定)'))
})

test('editing the meeting url and submitting sends the new value', async () => {
  const updateMock = mock.fn(() => Promise.resolve({ ...EDITABLE_RESERVATION }))
  reservationApi.updateReservation = updateMock

  renderPage()
  await screen.findByRole('form', { name: '予約編集フォーム' })

  fireEvent.change(screen.getByLabelText('オンライン会議URL'), {
    target: { value: 'https://example.com/meeting/updated' },
  })
  fireEvent.click(screen.getByRole('button', { name: '更新' }))

  await waitFor(() => assert.equal(updateMock.mock.calls.length, 1))
  assert.equal(
    updateMock.mock.calls[0].arguments[1].meeting_url,
    'https://example.com/meeting/updated',
  )
})

test('clearing the meeting url field sends null', async () => {
  reservationApi.getReservation = mock.fn(() =>
    Promise.resolve({ ...EDITABLE_RESERVATION, meeting_url: 'https://example.com/meeting/123' }),
  )
  const updateMock = mock.fn(() => Promise.resolve({ ...EDITABLE_RESERVATION }))
  reservationApi.updateReservation = updateMock

  renderPage()
  await screen.findByRole('form', { name: '予約編集フォーム' })

  fireEvent.change(screen.getByLabelText('オンライン会議URL'), { target: { value: '' } })
  fireEvent.click(screen.getByRole('button', { name: '更新' }))

  await waitFor(() => assert.equal(updateMock.mock.calls.length, 1))
  assert.equal(updateMock.mock.calls[0].arguments[1].meeting_url, null)
})

test('an invalid meeting url scheme while editing shows a validation error', async () => {
  renderPage()
  await screen.findByRole('form', { name: '予約編集フォーム' })

  fireEvent.change(screen.getByLabelText('オンライン会議URL'), {
    target: { value: 'ftp://example.com/meeting' },
  })
  fireEvent.click(screen.getByRole('button', { name: '更新' }))

  assert.ok(await screen.findByText('オンライン会議URLは http:// または https:// で始めてください'))
})
