// Unit tests for U002-T3 (docs/P007-impl-direction/U002-room-management.md).
// Target: RoomManagementPage component.
import './setupJsdom.ts'

import assert from 'node:assert/strict'
import { afterEach, beforeEach, mock, test } from 'node:test'

import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import React from 'react'
import { MemoryRouter } from 'react-router-dom'

import { authApi } from '../src/api/authApi.ts'
import { RoomManagementPage } from '../src/pages/RoomManagementPage.tsx'
import { roomApi, type Room } from '../src/api/roomApi.ts'

const SAMPLE_ROOM: Room = {
  room_id: 1,
  name: '会議室A',
  capacity: 8,
  equipment: ['プロジェクター'],
  description: '3階',
  is_active: true,
}

function mockAsAdmin() {
  authApi.getMe = mock.fn(() =>
    Promise.resolve({ employee_id: 'admin', name: 'システム管理者', role: 'admin' as const }),
  )
}

beforeEach(() => {
  roomApi.listRooms = mock.fn(() => Promise.resolve<Room[]>([]))
  roomApi.createRoom = mock.fn()
  roomApi.updateRoom = mock.fn()
  roomApi.deleteRoom = mock.fn()
})

afterEach(() => {
  cleanup()
  mock.reset()
})

function renderPage() {
  // U005-T4 added a <Header> (which calls useNavigate()) inside this page,
  // so it now needs a Router context even in isolation.
  return render(
    React.createElement(MemoryRouter, null, React.createElement(RoomManagementPage)),
  )
}

test('shows the room list fetched from the API for an admin user', async () => {
  mockAsAdmin()
  roomApi.listRooms = mock.fn(() => Promise.resolve([SAMPLE_ROOM]))

  renderPage()

  assert.ok(await screen.findByText('会議室A'))
  assert.ok(screen.getByRole('cell', { name: 'プロジェクター' }))
})

test('submitting the registration form with valid input calls roomApi.createRoom', async () => {
  mockAsAdmin()
  const createMock = mock.fn(() => Promise.resolve({ ...SAMPLE_ROOM, room_id: 2, name: '会議室B' }))
  roomApi.createRoom = createMock

  renderPage()
  await screen.findByRole('heading', { name: '会議室管理' })

  fireEvent.change(screen.getByLabelText('会議室名'), { target: { value: '会議室B' } })
  fireEvent.change(screen.getByLabelText('収容人数'), { target: { value: '6' } })
  fireEvent.click(screen.getByRole('button', { name: '登録' }))

  await waitFor(() => assert.equal(createMock.mock.calls.length, 1))
  assert.deepEqual(createMock.mock.calls[0].arguments[0], {
    name: '会議室B',
    capacity: 6,
    equipment: [],
    description: null,
  })
})

test('submitting with empty required fields shows validation errors and does not call the API', async () => {
  mockAsAdmin()
  const createMock = mock.fn()
  roomApi.createRoom = createMock

  renderPage()
  await screen.findByRole('heading', { name: '会議室管理' })

  fireEvent.click(screen.getByRole('button', { name: '登録' }))

  assert.ok(await screen.findByText('会議室名を入力してください'))
  assert.ok(screen.getByText('収容人数は1以上の整数で入力してください'))
  assert.equal(createMock.mock.calls.length, 0)
})

test('entering 0 or a negative capacity shows a validation error', async () => {
  mockAsAdmin()
  renderPage()
  await screen.findByRole('heading', { name: '会議室管理' })

  fireEvent.change(screen.getByLabelText('会議室名'), { target: { value: '会議室C' } })
  fireEvent.change(screen.getByLabelText('収容人数'), { target: { value: '0' } })
  fireEvent.click(screen.getByRole('button', { name: '登録' }))
  assert.ok(await screen.findByText('収容人数は1以上の整数で入力してください'))

  fireEvent.change(screen.getByLabelText('収容人数'), { target: { value: '-3' } })
  fireEvent.click(screen.getByRole('button', { name: '登録' }))
  assert.ok(await screen.findByText('収容人数は1以上の整数で入力してください'))
})

test('a general-role user sees the 403 screen instead of the room list', async () => {
  authApi.getMe = mock.fn(() =>
    Promise.resolve({ employee_id: 'u001', name: '一般 太郎', role: 'general' as const }),
  )

  renderPage()

  assert.ok(await screen.findByText('アクセス権がありません。'))
  assert.equal(screen.queryByRole('heading', { name: '会議室管理' }), null)
})
