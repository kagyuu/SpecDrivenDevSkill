// P103 integration test T004 (docs/P008-test-direction/T004-room-create-and-list.md).
// Renders the real RoomManagementPage (S06) against a real running server,
// then verifies the row directly in SQLite (node:sqlite, experimental but
// available in this Node runtime) - not just the API response.
import '../setupJsdom.ts'

import assert from 'node:assert/strict'
import { after, before, test } from 'node:test'
import { DatabaseSync } from 'node:sqlite'

import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import React from 'react'
import { MemoryRouter } from 'react-router-dom'

import { authApi } from '../../src/api/authApi.ts'
import { RoomManagementPage } from '../../src/pages/RoomManagementPage.tsx'
import { startRealServer, type RealServer } from './realServer.ts'

let server: RealServer

before(async () => {
  server = await startRealServer()
})

after(async () => {
  await server.stop()
})

test('registering a room via S06 saves it to the DB and reflects it in the list', async () => {
  await authApi.login('admin', 'ChangeMe123!')

  render(
    React.createElement(MemoryRouter, null, React.createElement(RoomManagementPage)),
  )

  await screen.findByRole('heading', { name: '会議室管理' })

  // 手順1
  fireEvent.change(screen.getByLabelText('会議室名'), { target: { value: '第一会議室' } })
  fireEvent.change(screen.getByLabelText('収容人数'), { target: { value: '8' } })
  fireEvent.click(screen.getByLabelText('プロジェクター'))
  fireEvent.click(screen.getByLabelText('ホワイトボード'))
  fireEvent.change(screen.getByLabelText('説明文'), { target: { value: '東棟3階' } })
  fireEvent.click(screen.getByRole('button', { name: '登録' }))

  // 手順2
  await screen.findByText('第一会議室')
  const row = screen.getByText('第一会議室').closest('tr')
  assert.ok(row)
  assert.ok(row?.textContent?.includes('8'))

  // 手順3
  const db = new DatabaseSync(server.dbPath, { readOnly: true });
  const dbRow = db
    .prepare('SELECT name, capacity, is_active FROM rooms WHERE name = ?')
    .get('第一会議室') as { name: string; capacity: number; is_active: number } | undefined
  db.close()
  assert.ok(dbRow)
  assert.equal(dbRow?.capacity, 8)
  assert.equal(dbRow?.is_active, 1)

  cleanup()
})
