// P201 acceptance test A011 (docs/P009-acceptance-direction/A011-error-handling-sequence.md).
// See authorizationCrosscheck.test.tsx for the naming/harness substitution note.
import '../setupJsdom.ts'

import assert from 'node:assert/strict'
import { after, before, test } from 'node:test'

import { fireEvent, render, screen } from '@testing-library/react'
import React from 'react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'

import { authApi } from '../../src/api/authApi.ts'
import { ReservationCreatePage } from '../../src/pages/ReservationCreatePage.tsx'
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
  // 既存予約(翌営業日10:00-11:00 相当。固定の将来日時を使う)
  await fetch('/api/reservations', {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      room_id: roomId,
      date: '2099-01-01',
      start_time: '10:00',
      end_time: '11:00',
      title: '既存予約',
      participant_user_ids: [],
      attendee_count: null,
      notes: null,
    }),
  })
})

after(async () => {
  await server.stop()
})

test(
  'validation errors -> fix -> conflict error -> fix -> success, without stale error/state leaking between steps',
  { timeout: 15_000 },
  async () => {
    render(
      React.createElement(
        MemoryRouter,
        { initialEntries: ['/reservations/new'] },
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

    // 手順1: 件名空欄、参加予定人数9(収容人数超過)、時間帯10:00-11:00(重複)
    fireEvent.change(screen.getByLabelText('会議室'), { target: { value: String(roomId) } })
    fireEvent.change(screen.getByLabelText('日付'), { target: { value: '2099-01-01' } })
    fireEvent.change(screen.getByLabelText('開始時刻'), { target: { value: '10:00' } })
    fireEvent.change(screen.getByLabelText('終了時刻'), { target: { value: '11:00' } })
    fireEvent.change(screen.getByLabelText('参加予定人数'), { target: { value: '9' } })
    fireEvent.click(screen.getByRole('button', { name: '登録' }))

    // 手順2: 件名必須・収容人数超過の両方が同時に表示される
    assert.ok(await screen.findByText('件名を入力してください'))
    assert.ok(screen.getByText('選択した会議室の収容人数(8名)を超えています'))

    // 手順3: 件名・参加予定人数を修正して再送信(時間帯はまだ重複したまま)
    fireEvent.change(screen.getByLabelText('件名'), { target: { value: 'テスト会議' } })
    fireEvent.change(screen.getByLabelText('参加予定人数'), { target: { value: '5' } })
    fireEvent.click(screen.getByRole('button', { name: '登録' }))

    // 手順4: 重複エラーのみが表示され、件名・収容人数エラーは解消。入力保持。
    assert.ok(await screen.findByText('選択した会議室・時間帯は既に予約されています'))
    assert.equal(screen.queryByText('件名を入力してください'), null)
    assert.equal(screen.queryByText('選択した会議室の収容人数(8名)を超えています'), null)
    assert.equal((screen.getByLabelText('件名') as HTMLInputElement).value, 'テスト会議')
    assert.equal((screen.getByLabelText('参加予定人数') as HTMLInputElement).value, '5')

    // 手順5: 時間帯を11:00-12:00に修正して登録
    fireEvent.change(screen.getByLabelText('開始時刻'), { target: { value: '11:00' } })
    fireEvent.change(screen.getByLabelText('終了時刻'), { target: { value: '12:00' } })
    fireEvent.click(screen.getByRole('button', { name: '登録' }))

    // 手順6: 成功(フォームがアンマウントされる=S02へ遷移)
    await new Promise((resolve) => setTimeout(resolve, 400))
    assert.equal(screen.queryByRole('form', { name: '予約作成フォーム' }), null)
  },
)
