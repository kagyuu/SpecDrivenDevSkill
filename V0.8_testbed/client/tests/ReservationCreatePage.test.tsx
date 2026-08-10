// Unit tests for U003-T5 (docs/P007-impl-direction/U003-reservation-core-and-calendar.md).
// Target: ReservationCreatePage.
import './setupJsdom.ts'

import assert from 'node:assert/strict'
import { afterEach, beforeEach, mock, test } from 'node:test'

import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import React from 'react'
import { MemoryRouter } from 'react-router-dom'

import {
  ReservationApiError,
  reservationApi,
  type ParticipantCandidate,
} from '../src/api/reservationApi.ts'
import { ReservationCreatePage } from '../src/pages/ReservationCreatePage.tsx'
import type { Room } from '../src/api/roomApi.ts'

const ROOM: Room = {
  room_id: 1,
  name: '会議室A',
  capacity: 4,
  equipment: [],
  description: null,
  is_active: true,
}

beforeEach(() => {
  reservationApi.listRooms = mock.fn(() => Promise.resolve<Room[]>([ROOM]))
  reservationApi.listParticipantCandidates = mock.fn(() =>
    Promise.resolve<ParticipantCandidate[]>([{ employee_id: 'u002', name: '参加 花子' }]),
  )
  reservationApi.createReservation = mock.fn()
})

afterEach(() => {
  cleanup()
  mock.reset()
})

function renderPage() {
  return render(
    React.createElement(MemoryRouter, null, React.createElement(ReservationCreatePage)),
  )
}

async function fillRequiredFields() {
  await screen.findByRole('option', { name: '会議室A' })
  fireEvent.change(screen.getByLabelText('会議室'), { target: { value: '1' } })
  fireEvent.change(screen.getByLabelText('日付'), { target: { value: '2099-01-01' } })
  fireEvent.change(screen.getByLabelText('開始時刻'), { target: { value: '10:00' } })
  fireEvent.change(screen.getByLabelText('終了時刻'), { target: { value: '11:00' } })
  fireEvent.change(screen.getByLabelText('件名'), { target: { value: '定例会議' } })
}

test('submitting a fully filled form calls createReservation with the entered values', async () => {
  const createMock = mock.fn(() =>
    Promise.resolve({
      reservation_id: 1,
      room_id: 1,
      room_name: '会議室A',
      organizer_user_id: 'admin',
      organizer_name: 'admin',
      date: '2099-01-01',
      start_time: '10:00',
      end_time: '11:00',
      title: '定例会議',
      participants: [],
      attendee_count: null,
      notes: null,
      meeting_url: null,
      editable: true,
    }),
  )
  reservationApi.createReservation = createMock

  renderPage()
  await fillRequiredFields()
  fireEvent.click(screen.getByRole('button', { name: '登録' }))

  await waitFor(() => assert.equal(createMock.mock.calls.length, 1))
  assert.deepEqual(createMock.mock.calls[0].arguments[0], {
    room_id: 1,
    date: '2099-01-01',
    start_time: '10:00',
    end_time: '11:00',
    title: '定例会議',
    participant_user_ids: [],
    attendee_count: null,
    notes: null,
    meeting_url: null,
  })
})

// CR-001 (docs/P901-cr-direction/CR-001.md, U003-T8) additions -------------

test('submitting with a valid meeting url sends it to createReservation', async () => {
  const createMock = mock.fn(() =>
    Promise.resolve({
      reservation_id: 1,
      room_id: 1,
      room_name: '会議室A',
      organizer_user_id: 'admin',
      organizer_name: 'admin',
      date: '2099-01-01',
      start_time: '10:00',
      end_time: '11:00',
      title: '定例会議',
      participants: [],
      attendee_count: null,
      notes: null,
      meeting_url: 'https://example.com/meeting/123',
      editable: true,
    }),
  )
  reservationApi.createReservation = createMock

  renderPage()
  await fillRequiredFields()
  fireEvent.change(screen.getByLabelText('オンライン会議URL'), {
    target: { value: 'https://example.com/meeting/123' },
  })
  fireEvent.click(screen.getByRole('button', { name: '登録' }))

  await waitFor(() => assert.equal(createMock.mock.calls.length, 1))
  assert.equal(
    createMock.mock.calls[0].arguments[0].meeting_url,
    'https://example.com/meeting/123',
  )
})

test('an invalid meeting url scheme shows a validation error and does not call the API', async () => {
  renderPage()
  await fillRequiredFields()
  fireEvent.change(screen.getByLabelText('オンライン会議URL'), {
    target: { value: 'ftp://example.com/meeting' },
  })

  fireEvent.click(screen.getByRole('button', { name: '登録' }))

  assert.ok(await screen.findByText('オンライン会議URLは http:// または https:// で始めてください'))
  assert.equal((reservationApi.createReservation as ReturnType<typeof mock.fn>).mock.calls.length, 0)
})

test('a 501-character meeting url shows a length validation error', async () => {
  renderPage()
  await fillRequiredFields()
  fireEvent.change(screen.getByLabelText('オンライン会議URL'), {
    target: { value: 'https://example.com/' + 'a'.repeat(501 - 'https://example.com/'.length) },
  })

  fireEvent.click(screen.getByRole('button', { name: '登録' }))

  assert.ok(await screen.findByText('オンライン会議URLは500文字以内で入力してください'))
})

test('checking the all-day checkbox auto-fills 09:00/18:00', async () => {
  renderPage()
  await screen.findByRole('option', { name: '会議室A' })

  fireEvent.click(screen.getByLabelText('終日'))

  assert.equal((screen.getByLabelText('開始時刻') as HTMLInputElement).value, '09:00')
  assert.equal((screen.getByLabelText('終了時刻') as HTMLInputElement).value, '18:00')
})

test('submitting without a title shows a validation error and does not call the API', async () => {
  renderPage()
  await screen.findByRole('option', { name: '会議室A' })
  fireEvent.change(screen.getByLabelText('会議室'), { target: { value: '1' } })
  fireEvent.change(screen.getByLabelText('日付'), { target: { value: '2099-01-01' } })
  fireEvent.change(screen.getByLabelText('開始時刻'), { target: { value: '10:00' } })
  fireEvent.change(screen.getByLabelText('終了時刻'), { target: { value: '11:00' } })

  fireEvent.click(screen.getByRole('button', { name: '登録' }))

  assert.ok(await screen.findByText('件名を入力してください'))
  assert.equal((reservationApi.createReservation as ReturnType<typeof mock.fn>).mock.calls.length, 0)
})

test('a 101-character title shows a length validation error', async () => {
  renderPage()
  await fillRequiredFields()
  fireEvent.change(screen.getByLabelText('件名'), { target: { value: 'x'.repeat(101) } })

  fireEvent.click(screen.getByRole('button', { name: '登録' }))

  assert.ok(await screen.findByText('件名は100文字以内で入力してください'))
})

test('an attendee count over the room capacity shows a validation error', async () => {
  renderPage()
  await fillRequiredFields()
  fireEvent.change(screen.getByLabelText('参加予定人数'), { target: { value: '5' } })

  fireEvent.click(screen.getByRole('button', { name: '登録' }))

  assert.ok(await screen.findByText('選択した会議室の収容人数(4名)を超えています'))
})

test('a 409 response shows the conflict message and keeps the entered values', async () => {
  reservationApi.createReservation = mock.fn(() =>
    Promise.reject(
      new ReservationApiError(409, {
        code: 'RESERVATION_CONFLICT',
        message: '選択した会議室・時間帯は既に予約されています',
      }),
    ),
  )

  renderPage()
  await fillRequiredFields()
  fireEvent.click(screen.getByRole('button', { name: '登録' }))

  assert.ok(await screen.findByText('選択した会議室・時間帯は既に予約されています'))
  assert.equal((screen.getByLabelText('件名') as HTMLInputElement).value, '定例会議')
})
