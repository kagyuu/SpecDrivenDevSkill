// Unit tests for U001-T5 (docs/P007-impl-direction/U001-foundation-and-auth.md).
// Target: LoginPage component.
//
// './setupJsdom.ts' MUST be the first import (see that file's own comment).
import './setupJsdom.ts'

import assert from 'node:assert/strict'
import { afterEach, beforeEach, mock, test } from 'node:test'

import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import React from 'react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'

import { AuthApiError, authApi } from '../src/api/authApi.ts'
import { LoginPage } from '../src/pages/LoginPage.tsx'

beforeEach(() => {
  // Default: "not logged in" so LoginPage's mount-time redirect check
  // (docs/P002-frontend-spec.md 3.1節 動作4) does not fire during tests
  // that are exercising the form itself.
  authApi.getMe = mock.fn(() => Promise.reject(new Error('not logged in')))
})

afterEach(() => {
  cleanup()
  mock.reset()
})

function renderLoginPage() {
  return render(
    React.createElement(MemoryRouter, null, React.createElement(LoginPage, null)),
  )
}

test('submitting with entered employee id and password calls authApi.login with those values', async () => {
  const loginMock = mock.fn(() =>
    Promise.resolve({ employee_id: 'u001', name: 'Taro', role: 'general' as const }),
  )
  authApi.login = loginMock

  renderLoginPage()

  fireEvent.change(screen.getByLabelText('社員ID'), { target: { value: 'u001' } })
  fireEvent.change(screen.getByLabelText('パスワード'), {
    target: { value: 'password123' },
  })
  fireEvent.click(screen.getByRole('button', { name: 'ログイン' }))

  await waitFor(() => assert.equal(loginMock.mock.calls.length, 1))
  assert.deepEqual(loginMock.mock.calls[0].arguments, ['u001', 'password123'])
})

test('submitting with empty fields shows validation messages and does not call the API', async () => {
  const loginMock = mock.fn()
  authApi.login = loginMock

  renderLoginPage()

  fireEvent.click(screen.getByRole('button', { name: 'ログイン' }))

  assert.ok(await screen.findByText('社員IDを入力してください'))
  assert.ok(screen.getByText('パスワードを入力してください'))
  assert.equal(loginMock.mock.calls.length, 0)
})

test('a 401 response from the API shows the generic credentials error message', async () => {
  authApi.login = mock.fn(() =>
    Promise.reject(
      new AuthApiError(401, {
        code: 'INVALID_CREDENTIALS',
        message: '社員IDまたはパスワードが正しくありません',
      }),
    ),
  )

  renderLoginPage()

  fireEvent.change(screen.getByLabelText('社員ID'), { target: { value: 'u001' } })
  fireEvent.change(screen.getByLabelText('パスワード'), {
    target: { value: 'wrong-password' },
  })
  fireEvent.click(screen.getByRole('button', { name: 'ログイン' }))

  assert.ok(await screen.findByText('社員IDまたはパスワードが正しくありません'))
})

test('already-authenticated visitors are redirected away from the login form', async () => {
  // docs/P002-frontend-spec.md 3.1節 動作4. Needs real <Routes>/<Route> (unlike
  // the other tests above, which render LoginPage directly) so the redirect
  // triggered by navigate('/') is observable as a change in rendered output.
  authApi.getMe = mock.fn(() =>
    Promise.resolve({ employee_id: 'admin', name: 'システム管理者', role: 'admin' as const }),
  )

  render(
    React.createElement(
      MemoryRouter,
      { initialEntries: ['/login'] },
      React.createElement(
        Routes,
        null,
        React.createElement(Route, { path: '/login', element: React.createElement(LoginPage) }),
        React.createElement(Route, { path: '/', element: React.createElement('div', null, 'HOME') }),
      ),
    ),
  )

  assert.ok(await screen.findByText('HOME'))
  assert.equal(screen.queryByRole('heading', { name: 'ログイン' }), null)
})
