// P103 integration test T012 (docs/P008-test-direction/T012-mylist-period-filter.md).
// Real MyReservationsPage against a real server.
//
// ★実施メモ: T012の【使用するテストデータ】は過去の予約を「DBへ直接INSERT」
// して用意するよう指示しているが、`node:sqlite`(Node実験的機能)の
// DatabaseSyncを同一プロセスでjsdom+React再描画と併用するとイベントループが
// 停止する現象を確認した(調査の結果、テスト対象コードの不具合ではなく
// node:sqlite側の実験的実装に起因すると判断)。`server/app/services/reservation_service.py`
// のバリデーションは過去日付を拒否しない(3.3節のクライアント側ルールであり、
// 4.7節がサーバー側に要求する再検証項目には該当しない実装になっている)ため、
// 実サーバーへの通常のPOST /api/reservationsで過去日付の予約を作成できる。
// 本テストではDB直接操作の代わりにこの経路を使い、同じ最終状態(過去の予約が
// 1件存在する)を安定して再現する。
//
// ★実施メモ2: 当初、予約の件名に「過去の予約」「未来の予約」という文字列を
// 使っていたが、これは期間フィルタのラジオボタンのラベル文字列
// (「過去の予約」「今後の予約」)と衝突し、`screen.queryByText(...)`が複数要素に
// マッチして極端に低速化する(事実上ハングする)現象を引き起こした。件名は
// フィルタのラベルと重複しない文字列に変更し、かつ一覧の`<table>`スコープに
// 限定してクエリすることで曖昧一致を避けている。
import '../setupJsdom.ts'

import assert from 'node:assert/strict'
import { after, before, test } from 'node:test'

import { cleanup, fireEvent, render, screen, within } from '@testing-library/react'
import React from 'react'
import { MemoryRouter } from 'react-router-dom'

import { authApi } from '../../src/api/authApi.ts'
import { MyReservationsPage } from '../../src/pages/MyReservationsPage.tsx'
import { startRealServer, type RealServer } from './realServer.ts'

let server: RealServer

const UPCOMING_TITLE = '来月分の定例会議'
const PAST_TITLE = '先月分の定例会議'

before(async () => {
  server = await startRealServer()
  await authApi.login('admin', 'ChangeMe123!')
  const roomId = (
    await (
      await fetch('/api/rooms', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: '第一会議室', capacity: 8, equipment: [], description: null }),
      })
    ).json()
  ).room_id

  await fetch('/api/reservations', {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      room_id: roomId,
      date: '2099-01-01',
      start_time: '10:00',
      end_time: '11:00',
      title: UPCOMING_TITLE,
      participant_user_ids: [],
      attendee_count: null,
      notes: null,
    }),
  })

  // 過去の予約(上記メモのとおりAPI経由で作成 - サーバー側は過去日付を拒否しない)
  await fetch('/api/reservations', {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      room_id: roomId,
      date: '2020-01-01',
      start_time: '10:00',
      end_time: '11:00',
      title: PAST_TITLE,
      participant_user_ids: [],
      attendee_count: null,
      notes: null,
    }),
  })
})

after(async () => {
  await server.stop()
})

test('the period filter switches between upcoming/past/all correctly', { timeout: 15_000 }, async () => {
  render(React.createElement(MemoryRouter, null, React.createElement(MyReservationsPage)))
  const table = () => screen.getByRole('table')

  // 手順1: 既定(今後の予約)
  assert.ok(await within(table()).findByText(UPCOMING_TITLE))
  assert.equal(within(table()).queryByText(PAST_TITLE), null)

  // 手順2
  fireEvent.click(screen.getByLabelText('過去の予約'))
  await within(table()).findByText(PAST_TITLE)
  assert.equal(within(table()).queryByText(UPCOMING_TITLE), null)

  // 手順3
  fireEvent.click(screen.getByLabelText('すべて'))
  await within(table()).findByText(UPCOMING_TITLE)
  assert.ok(within(table()).getByText(PAST_TITLE))

  cleanup()
})
