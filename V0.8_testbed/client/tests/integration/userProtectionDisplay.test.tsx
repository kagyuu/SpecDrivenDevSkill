// P103 integration test T014 (docs/P008-test-direction/T014-user-protection-display.md).
// Real UserManagementPage against a real server: admin tries to deactivate
// themselves while being the only admin, and the resulting error code/
// message must be SELF_DEACTIVATION_FORBIDDEN (not LAST_ADMIN_PROTECTED),
// confirming the judgment order from docs/P003-backend-spec.md 4.11〜4.11.2節.
import '../setupJsdom.ts'

import assert from 'node:assert/strict'
import { after, before, test } from 'node:test'

import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import React from 'react'
import { MemoryRouter } from 'react-router-dom'

import { authApi } from '../../src/api/authApi.ts'
import { UserManagementPage } from '../../src/pages/UserManagementPage.tsx'
import { startRealServer, type RealServer } from './realServer.ts'

let server: RealServer

before(async () => {
  server = await startRealServer()
  await authApi.login('admin', 'ChangeMe123!')
})

after(async () => {
  await server.stop()
})

test(
  'the sole admin trying to deactivate themselves sees SELF_DEACTIVATION_FORBIDDEN, not LAST_ADMIN_PROTECTED',
  { timeout: 15_000 },
  async () => {
    render(React.createElement(MemoryRouter, null, React.createElement(UserManagementPage)))
    await screen.findByText('admin')

    // 手順1
    const originalConfirm = window.confirm
    window.confirm = () => true
    fireEvent.click(screen.getAllByRole('button', { name: '削除' })[0])

    // 手順2
    assert.ok(await screen.findByText('自分自身は無効化できません'))
    assert.equal(screen.queryByText('最後の管理者アカウントは無効化できません'), null)
    window.confirm = originalConfirm

    // Independently confirm the error code via the API directly (手順3の
    // 判定順序確認 - SELF_DEACTIVATION_FORBIDDEN であって
    // LAST_ADMIN_PROTECTED ではないこと)。
    const response = await fetch('/api/users/admin', {
      method: 'PUT',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: 'システム管理者', password: null, role: 'admin', is_active: false }),
    })
    const body = await response.json()
    assert.equal(response.status, 400)
    assert.equal(body.error.code, 'SELF_DEACTIVATION_FORBIDDEN')

    cleanup()
  },
)
