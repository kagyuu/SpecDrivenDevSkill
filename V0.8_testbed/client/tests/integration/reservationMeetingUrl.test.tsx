// P103 integration test T016 (docs/P008-test-direction/T016-reservation-meeting-url.md).
// CR-001 (docs/P901-cr-direction/CR-001.md): S03(作成)→S04(表示・編集)→DBまで
// オンライン会議URLが一貫して連携することを確認する。
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
import { startRealServer, type RealServer } from './realServer.ts'

let server: RealServer
let roomId: number

function tomorrowIsoDate(): string {
  const date = new Date()
  date.setDate(date.getDate() + 1)
  return date.toISOString().slice(0, 10)
}

const TEST_DATE = tomorrowIsoDate()
const INITIAL_URL = 'https://example.com/meeting/cr001'
const UPDATED_URL = 'https://example.com/meeting/cr001-updated'

before(async () => {
  server = await startRealServer()

  await authApi.login('admin', 'ChangeMe123!')
  const roomResponse = await fetch('/api/rooms', {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name: '第一会議室', capacity: 8, equipment: [], description: null }),
  })
  roomId = (await roomResponse.json()).room_id
  // 予約者(admin)と無関係な一般ユーザーを1件登録する。読み取り専用表示(リンク
  // 表示)は「予約者本人でも管理者でもない」ユーザーでのみ現れる(3.4節、
  // ReservationDetailPage.tsxのeditable分岐)。organizer(admin)自身は常に編集
  // フォーム側(テキスト入力欄)に入るため、リンク表示の確認にはこの別ユーザーが
  // 必要。
  await fetch('/api/users', {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ employee_id: 'u001', name: '一般 太郎', password: 'Password1!', role: 'general' }),
  })
  await authApi.logout()
})

after(async () => {
  await server.stop()
})

function renderDetailPage(reservationId: number) {
  return render(
    React.createElement(
      MemoryRouter,
      { initialEntries: [`/reservations/${reservationId}`] },
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

test('meeting url survives S03 create -> DB -> S04 display -> edit -> clear', async () => {
  await authApi.login('admin', 'ChangeMe123!')

  // 手順1: S03で登録する。
  render(
    React.createElement(
      MemoryRouter,
      { initialEntries: [`/reservations/new?room_id=${roomId}&date=${TEST_DATE}&start_time=13:00`] },
      React.createElement(
        Routes,
        null,
        React.createElement(Route, {
          path: '/reservations/new',
          element: React.createElement(ReservationCreatePage),
        }),
      ),
    ),
  )
  await screen.findByRole('option', { name: '第一会議室' })
  fireEvent.change(screen.getByLabelText('終了時刻'), { target: { value: '14:00' } })
  fireEvent.change(screen.getByLabelText('件名'), { target: { value: 'CR-001確認用会議' } })
  fireEvent.change(screen.getByLabelText('オンライン会議URL'), { target: { value: INITIAL_URL } })
  fireEvent.click(screen.getByRole('button', { name: '登録' }))

  await new Promise((resolve) => setTimeout(resolve, 300))
  assert.equal(screen.queryByRole('form', { name: '予約作成フォーム' }), null)
  cleanup()

  // 手順2: DBを直接確認する。
  const db = new DatabaseSync(server.dbPath, { readOnly: true })
  const row = db
    .prepare("SELECT reservation_id, meeting_url FROM reservations WHERE title = 'CR-001確認用会議'")
    .get() as { reservation_id: number; meeting_url: string } | undefined
  db.close()
  assert.ok(row, 'expected a reservations row for CR-001確認用会議')
  assert.equal(row?.meeting_url, INITIAL_URL)
  const reservationId = row!.reservation_id

  // 手順3: GET /api/reservations(一覧)にmeeting_urlが含まれないことを確認する。
  const listResponse = await fetch(
    `/api/reservations?date_from=${TEST_DATE}&date_to=${TEST_DATE}`,
    { credentials: 'include' },
  )
  const listBody = await listResponse.json()
  for (const item of listBody) {
    assert.ok(!('meeting_url' in item))
  }

  // 手順4: S04でリンク表示されることを確認する(予約者(admin)自身は編集フォーム
  // 側に入るため、無関係な一般ユーザー(u001)としてログインして読み取り専用表示
  // を確認する)。
  await authApi.logout()
  await authApi.login('u001', 'Password1!')
  renderDetailPage(reservationId)
  const link = (await screen.findByText(INITIAL_URL)) as HTMLAnchorElement
  assert.equal(link.tagName, 'A')
  assert.equal(link.getAttribute('href'), INITIAL_URL)
  cleanup()
  await authApi.logout()

  // 手順5: adminとして編集フォームでURLを変更して更新する。
  await authApi.login('admin', 'ChangeMe123!')
  renderDetailPage(reservationId)
  await screen.findByRole('form', { name: '予約編集フォーム' })
  fireEvent.change(screen.getByLabelText('オンライン会議URL'), { target: { value: UPDATED_URL } })
  fireEvent.click(screen.getByRole('button', { name: '更新' }))
  await new Promise((resolve) => setTimeout(resolve, 300))
  cleanup()
  await authApi.logout()

  // 手順6: 再度u001でS04を開き、更新後のURLがリンク表示されることを確認する。
  await authApi.login('u001', 'Password1!')
  renderDetailPage(reservationId)
  const updatedLink = (await screen.findByText(UPDATED_URL)) as HTMLAnchorElement
  assert.equal(updatedLink.getAttribute('href'), UPDATED_URL)
  cleanup()
  await authApi.logout()

  // 手順7: adminとして編集フォームで空欄にして更新する。
  await authApi.login('admin', 'ChangeMe123!')
  renderDetailPage(reservationId)
  await screen.findByRole('form', { name: '予約編集フォーム' })
  fireEvent.change(screen.getByLabelText('オンライン会議URL'), { target: { value: '' } })
  fireEvent.click(screen.getByRole('button', { name: '更新' }))
  await new Promise((resolve) => setTimeout(resolve, 300))
  cleanup()
  await authApi.logout()

  // 手順8: u001で見て「(未設定)」表示、DBがNULLであることを確認する。
  await authApi.login('u001', 'Password1!')
  renderDetailPage(reservationId)
  assert.ok(await screen.findByText('(未設定)'))
  cleanup()

  const db2 = new DatabaseSync(server.dbPath, { readOnly: true })
  const row2 = db2
    .prepare('SELECT meeting_url FROM reservations WHERE reservation_id = ?')
    .get(reservationId) as { meeting_url: string | null } | undefined
  db2.close()
  assert.equal(row2?.meeting_url, null)
})
