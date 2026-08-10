// Unit tests for U005-T3 (docs/P007-impl-direction/U005-user-management-and-hardening.md).
// Target: UserManagementPage.
import './setupJsdom.ts'

import assert from 'node:assert/strict'
import { afterEach, beforeEach, mock, test } from 'node:test'

import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import React from 'react'
import { MemoryRouter } from 'react-router-dom'

import { authApi } from '../src/api/authApi.ts'
import { UserManagementPage } from '../src/pages/UserManagementPage.tsx'
import { userApi, UserApiError, type ManagedUser } from '../src/api/userApi.ts'

const SAMPLE_USER: ManagedUser = {
  employee_id: 'u001',
  name: '一般 太郎',
  role: 'general',
  is_active: true,
}

function mockAsAdmin() {
  authApi.getMe = mock.fn(() =>
    Promise.resolve({ employee_id: 'admin', name: 'システム管理者', role: 'admin' as const }),
  )
}

beforeEach(() => {
  userApi.listUsers = mock.fn(() => Promise.resolve<ManagedUser[]>([]))
  userApi.createUser = mock.fn()
  userApi.updateUser = mock.fn()
  userApi.deleteUser = mock.fn()
})

afterEach(() => {
  cleanup()
  mock.reset()
})

function renderPage() {
  // U005-T4 added a <Header> (which calls useNavigate()) inside this page,
  // so it now needs a Router context even in isolation.
  return render(
    React.createElement(MemoryRouter, null, React.createElement(UserManagementPage)),
  )
}

test('shows the user list fetched from the API for an admin user', async () => {
  mockAsAdmin()
  userApi.listUsers = mock.fn(() => Promise.resolve([SAMPLE_USER]))

  renderPage()

  assert.ok(await screen.findByText('u001'))
  assert.ok(screen.getByText('一般 太郎'))
})

test('submitting the registration form with valid input calls userApi.createUser', async () => {
  mockAsAdmin()
  const createMock = mock.fn(() =>
    Promise.resolve({ employee_id: 'u002', name: '一般 花子', role: 'general' as const, is_active: true }),
  )
  userApi.createUser = createMock

  renderPage()
  await screen.findByRole('heading', { name: 'ユーザー管理' })

  fireEvent.change(screen.getByLabelText('社員ID'), { target: { value: 'u002' } })
  fireEvent.change(screen.getByLabelText('氏名'), { target: { value: '一般 花子' } })
  fireEvent.change(screen.getByLabelText('パスワード'), { target: { value: 'Password1!' } })
  fireEvent.click(screen.getByRole('button', { name: '登録' }))

  await waitFor(() => assert.equal(createMock.mock.calls.length, 1))
  assert.deepEqual(createMock.mock.calls[0].arguments[0], {
    employee_id: 'u002',
    name: '一般 花子',
    password: 'Password1!',
    role: 'general',
  })
})

test('submitting without an employee id or with a short password shows validation errors', async () => {
  mockAsAdmin()
  renderPage()
  await screen.findByRole('heading', { name: 'ユーザー管理' })

  fireEvent.change(screen.getByLabelText('氏名'), { target: { value: '一般 花子' } })
  fireEvent.change(screen.getByLabelText('パスワード'), { target: { value: 'short1' } })
  fireEvent.click(screen.getByRole('button', { name: '登録' }))

  assert.ok(await screen.findByText('社員IDを入力してください'))
  assert.ok(screen.getByText('パスワードは8文字以上で入力してください'))
})

test('a SELF_DEACTIVATION_FORBIDDEN response shows the mapped message', async () => {
  mockAsAdmin()
  userApi.listUsers = mock.fn(() => Promise.resolve([SAMPLE_USER]))
  userApi.deleteUser = mock.fn(() =>
    Promise.reject(
      new UserApiError(400, { code: 'SELF_DEACTIVATION_FORBIDDEN', message: 'x' }),
    ),
  )
  const originalConfirm = window.confirm
  window.confirm = () => true

  renderPage()
  await screen.findByText('u001')
  fireEvent.click(screen.getByRole('button', { name: '削除' }))

  assert.ok(await screen.findByText('自分自身は無効化できません'))
  window.confirm = originalConfirm
})

test('a LAST_ADMIN_PROTECTED response shows the mapped message', async () => {
  mockAsAdmin()
  userApi.listUsers = mock.fn(() => Promise.resolve([SAMPLE_USER]))
  userApi.deleteUser = mock.fn(() =>
    Promise.reject(new UserApiError(400, { code: 'LAST_ADMIN_PROTECTED', message: 'x' })),
  )
  const originalConfirm = window.confirm
  window.confirm = () => true

  renderPage()
  await screen.findByText('u001')
  fireEvent.click(screen.getByRole('button', { name: '削除' }))

  assert.ok(await screen.findByText('最後の管理者アカウントは無効化できません'))
  window.confirm = originalConfirm
})

test('a general-role user sees the 403 screen instead of the user list', async () => {
  authApi.getMe = mock.fn(() =>
    Promise.resolve({ employee_id: 'u001', name: '一般 太郎', role: 'general' as const }),
  )

  renderPage()

  assert.ok(await screen.findByText('アクセス権がありません。'))
  assert.equal(screen.queryByRole('heading', { name: 'ユーザー管理' }), null)
})
