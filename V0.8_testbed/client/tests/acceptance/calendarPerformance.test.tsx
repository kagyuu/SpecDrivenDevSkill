// P201 acceptance test A006 (docs/P009-acceptance-direction/A006-calendar-performance.md).
//
// ★実施メモ: 仕様はPlaywright等のヘッドレスブラウザでの計測を想定しているが、
// 本ラウンドではPlaywrightのセットアップを新規に行う時間的余裕が無いため見送り、
// authorizationCrosscheck.test.tsx と同じjsdom + 実サーバーの手法で代替した
// (これによりネットワーク往復・ブラウザレンダリングの実際のコストは反映されない
// ため、この計測値はもとより「参考値」であるという仕様自身の位置づけを、
// より強い意味で受け継ぐことになる)。
import '../setupJsdom.ts'

import assert from 'node:assert/strict'
import { after, before, test } from 'node:test'

import { cleanup, render, screen } from '@testing-library/react'
import React from 'react'
import { MemoryRouter } from 'react-router-dom'

import { authApi } from '../../src/api/authApi.ts'
import { CalendarPage } from '../../src/pages/CalendarPage.tsx'
import { startRealServer, type RealServer } from '../integration/realServer.ts'

let server: RealServer

function todayIsoDate(): string {
  return new Date().toISOString().slice(0, 10)
}

before(async () => {
  server = await startRealServer()
  await authApi.login('admin', 'ChangeMe123!')

  const roomIds: number[] = []
  for (let i = 0; i < 10; i += 1) {
    const response = await fetch('/api/rooms', {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: `会議室${i + 1}`, capacity: 8, equipment: [], description: null }),
    })
    roomIds.push((await response.json()).room_id)
  }

  // 直近1週間分・約150件の予約をシードする(各会議室・各日で数枠ずつ)。
  const today = todayIsoDate()
  let created = 0
  outer: for (let dayOffset = 0; dayOffset < 7; dayOffset += 1) {
    const date = new Date(`${today}T00:00:00Z`)
    date.setUTCDate(date.getUTCDate() + dayOffset)
    const dateStr = date.toISOString().slice(0, 10)
    for (const roomId of roomIds) {
      for (let slot = 0; slot < 3; slot += 1) {
        if (created >= 150) break outer
        const startHour = 9 + slot * 3
        await fetch('/api/reservations', {
          method: 'POST',
          credentials: 'include',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            room_id: roomId,
            date: dateStr,
            start_time: `${String(startHour).padStart(2, '0')}:00`,
            end_time: `${String(startHour + 1).padStart(2, '0')}:00`,
            title: `性能検証予約${created + 1}`,
            participant_user_ids: [],
            attendee_count: null,
            notes: null,
          }),
        })
        created += 1
      }
    }
  }
})

after(async () => {
  await server.stop()
})

test('rendering S02 with ~150 seeded reservations completes within 3 seconds (reference measurement)', { timeout: 15_000 }, async () => {
  const measurements: number[] = []

  for (let round = 0; round < 3; round += 1) {
    const start = performance.now()
    render(React.createElement(MemoryRouter, null, React.createElement(CalendarPage)))
    await screen.findByRole('heading', { name: '予約カレンダー' })
    // グリッド内の予約セル(空きセルではないbutton)が最低1件描画されるまで待つ。
    await screen.findAllByRole('button', { name: /性能検証予約/ })
    const elapsed = performance.now() - start
    measurements.push(elapsed)
    cleanup()
  }

  console.log('A006 measurements (ms, reference only):', measurements)
  assert.ok(
    measurements.every((ms) => ms < 3000),
    `expected all 3 measurements under 3000ms, got ${JSON.stringify(measurements)}`,
  )
})
