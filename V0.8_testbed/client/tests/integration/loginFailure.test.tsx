// P103 integration test T002 (docs/P008-test-direction/T002-login-failure-display.md).
// Renders the real LoginPage against a real running server (no API
// mocking) - see realServer.ts for how relative fetch() calls and cookies
// are made to work under Node's test runner.
import '../setupJsdom.ts'

import assert from 'node:assert/strict'
import { after, before, test } from 'node:test'

import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import React from 'react'
import { MemoryRouter } from 'react-router-dom'

import { LoginPage } from '../../src/pages/LoginPage.tsx'
import { startRealServer, type RealServer } from './realServer.ts'

let server: RealServer

before(async () => {
  server = await startRealServer()
})

after(async () => {
  await server.stop()
})

function renderLoginPage() {
  return render(
    React.createElement(MemoryRouter, null, React.createElement(LoginPage)),
  )
}

async function attemptLogin(employeeId: string, password: string) {
  fireEvent.change(screen.getByLabelText('社員ID'), { target: { value: employeeId } })
  fireEvent.change(screen.getByLabelText('パスワード'), { target: { value: password } })
  fireEvent.click(screen.getByRole('button', { name: 'ログイン' }))
  await screen.findByText('社員IDまたはパスワードが正しくありません')
}

test('a nonexistent employee id shows the generic credentials error and stays on S01', async () => {
  server.resetSession()
  renderLoginPage()

  await attemptLogin('nonexistent', 'whatever123')

  assert.ok(screen.getByRole('heading', { name: 'ログイン' }))
  cleanup()
})

test('a correct employee id with the wrong password shows the SAME generic error', async () => {
  server.resetSession()
  renderLoginPage()

  await attemptLogin('admin', 'wrongpass')

  assert.ok(screen.getByText('社員IDまたはパスワードが正しくありません'))
  assert.ok(screen.getByRole('heading', { name: 'ログイン' }))
  cleanup()
})
