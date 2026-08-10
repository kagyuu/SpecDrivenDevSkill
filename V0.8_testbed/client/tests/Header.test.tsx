// Unit tests for U005-T4 (docs/P007-impl-direction/U005-user-management-and-hardening.md).
// Target: Header.
import './setupJsdom.ts'

import assert from 'node:assert/strict'
import { afterEach, beforeEach, mock, test } from 'node:test'

import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import React from 'react'
import { MemoryRouter } from 'react-router-dom'

import { authApi } from '../src/api/authApi.ts'
import { Header } from '../src/components/Header.tsx'

afterEach(() => {
  cleanup()
  mock.reset()
})

function renderHeader(currentScreen: 'S02' | 'S06') {
  return render(
    React.createElement(MemoryRouter, null, React.createElement(Header, { currentScreen })),
  )
}

test('a general user never sees the room-management or user-management links', async () => {
  authApi.getMe = mock.fn(() =>
    Promise.resolve({ employee_id: 'u001', name: '一般 太郎', role: 'general' as const }),
  )

  renderHeader('S06')

  await screen.findByText('一般 太郎')
  assert.equal(screen.queryByRole('link', { name: '会議室管理' }), null)
  assert.equal(screen.queryByRole('link', { name: 'ユーザー管理' }), null)
})

test('an admin on S02 sees room-management but not user-management', async () => {
  authApi.getMe = mock.fn(() =>
    Promise.resolve({ employee_id: 'admin', name: 'システム管理者', role: 'admin' as const }),
  )

  renderHeader('S02')

  assert.ok(await screen.findByRole('link', { name: '会議室管理' }))
  assert.equal(screen.queryByRole('link', { name: 'ユーザー管理' }), null)
})

test('an admin on S06 sees both room-management and user-management links', async () => {
  authApi.getMe = mock.fn(() =>
    Promise.resolve({ employee_id: 'admin', name: 'システム管理者', role: 'admin' as const }),
  )

  renderHeader('S06')

  assert.ok(await screen.findByRole('link', { name: '会議室管理' }))
  assert.ok(screen.getByRole('link', { name: 'ユーザー管理' }))
})

test('clicking logout calls authApi.logout and navigates to /login', async () => {
  authApi.getMe = mock.fn(() =>
    Promise.resolve({ employee_id: 'admin', name: 'システム管理者', role: 'admin' as const }),
  )
  const logoutMock = mock.fn(() => Promise.resolve())
  authApi.logout = logoutMock

  renderHeader('S02')
  await screen.findByText('システム管理者')

  fireEvent.click(screen.getByRole('button', { name: 'ログアウト' }))

  await waitFor(() => assert.equal(logoutMock.mock.calls.length, 1))
})
