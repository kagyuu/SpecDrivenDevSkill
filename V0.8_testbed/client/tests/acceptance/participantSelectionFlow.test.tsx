// P201 acceptance test A004 (docs/P009-acceptance-direction/A004-participant-selection-flow.md).
// See authorizationCrosscheck.test.tsx for the naming/harness substitution note.
import '../setupJsdom.ts'

import assert from 'node:assert/strict'
import { after, before, test } from 'node:test'
import { DatabaseSync } from 'node:sqlite'

import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import React from 'react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'

import { authApi } from '../../src/api/authApi.ts'
import { ReservationCreatePage } from '../../src/pages/ReservationCreatePage.tsx'
import { ReservationDetailPage } from '../../src/pages/ReservationDetailPage.tsx'
import { startRealServer, type RealServer } from '../integration/realServer.ts'

let server: RealServer
let roomId: number

before(async () => {
  server = await startRealServer()
  await authApi.login('admin', 'ChangeMe123!')
  roomId = (
    await (
      await fetch('/api/rooms', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: '第一会議室', capacity: 8, equipment: [], description: null }),
      })
    ).json()
  ).room_id
  // 「鈴木花子」(e2002)を登録
  await fetch('/api/users', {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ employee_id: 'e2002', name: '鈴木花子', password: 'Password1!', role: 'general' }),
  })
  // 予約者本人(別の一般ユーザー)を登録
  await fetch('/api/users', {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ employee_id: 'e1001', name: '予約者太郎', password: 'Password1!', role: 'general' }),
  })
  await authApi.logout()
  await authApi.login('e1001', 'Password1!')
})

after(async () => {
  await server.stop()
})

test(
  'selecting a directory participant on S03 saves and displays them on S04, and reservation_participants has the row',
  { timeout: 15_000 },
  async () => {
    // 手順1: 参加者候補一覧に鈴木花子が社員ID・氏名のみで表示される
    const directoryResponse = await fetch('/api/users/directory', { credentials: 'include' })
    const directory = await directoryResponse.json()
    const hanako = directory.find((entry: { employee_id: string }) => entry.employee_id === 'e2002')
    assert.ok(hanako)
    assert.deepEqual(Object.keys(hanako).sort(), ['employee_id', 'name'])

    render(
      React.createElement(MemoryRouter, null, React.createElement(ReservationCreatePage)),
    )
    await screen.findByRole('option', { name: '第一会議室' })
    await screen.findByLabelText('鈴木花子')

    fireEvent.change(screen.getByLabelText('会議室'), { target: { value: String(roomId) } })
    fireEvent.change(screen.getByLabelText('日付'), { target: { value: '2099-01-01' } })
    fireEvent.change(screen.getByLabelText('開始時刻'), { target: { value: '10:00' } })
    fireEvent.change(screen.getByLabelText('終了時刻'), { target: { value: '11:00' } })
    fireEvent.change(screen.getByLabelText('件名'), { target: { value: '定例会議' } })
    fireEvent.click(screen.getByLabelText('鈴木花子'))
    fireEvent.click(screen.getByRole('button', { name: '登録' }))

    await new Promise((resolve) => setTimeout(resolve, 400))
    cleanup()

    // 手順4: DB確認
    const db = new DatabaseSync(server.dbPath, { readOnly: true })
    const row = db
      .prepare(
        `SELECT rp.user_id FROM reservation_participants rp
         JOIN reservations r ON r.reservation_id = rp.reservation_id
         WHERE r.title = '定例会議'`,
      )
      .get() as { user_id: string } | undefined
    db.close()
    assert.ok(row, 'expected a reservation_participants row for the new reservation')
    assert.equal(row?.user_id, 'e2002')

    // 手順3: S04の参加者一覧
    const listResponse = await fetch('/api/reservations/mine?period=all', { credentials: 'include' })
    const [created] = await listResponse.json()
    assert.ok(created)

    render(
      React.createElement(
        MemoryRouter,
        { initialEntries: [`/reservations/${created.reservation_id}`] },
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
    await screen.findByRole('form', { name: '予約編集フォーム' })
    assert.ok(screen.getByLabelText('鈴木花子') as HTMLInputElement)
    assert.equal((screen.getByLabelText('鈴木花子') as HTMLInputElement).checked, true)
    cleanup()
  },
)
