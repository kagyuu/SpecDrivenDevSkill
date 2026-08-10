// P103 integration test T013 (docs/P008-test-direction/T013-user-crud.md).
// Real UserManagementPage (S07) against a real server: register, edit,
// deactivate, then verify the SQLite row directly.
import '../setupJsdom.ts'

import assert from 'node:assert/strict'
import { after, before, test } from 'node:test'
import { DatabaseSync } from 'node:sqlite'

import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
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
  'registering, editing, and deactivating a user via S07 is reflected in the list and the DB',
  { timeout: 15_000 },
  async () => {
    render(React.createElement(MemoryRouter, null, React.createElement(UserManagementPage)))
    await screen.findByRole('heading', { name: 'ユーザー管理' })

    // 手順1
    fireEvent.change(screen.getByLabelText('社員ID'), { target: { value: 'e1001' } })
    fireEvent.change(screen.getByLabelText('氏名'), { target: { value: '山田太郎' } })
    fireEvent.change(screen.getByLabelText('パスワード'), { target: { value: 'Passw0rd!' } })
    fireEvent.click(screen.getByRole('button', { name: '登録' }))

    // 手順2
    await screen.findByText('山田太郎')

    // 手順3: 編集(パスワードは空欄のまま)。★実施メモ: 一覧には`admin`(seed
    // データ)と`e1001`の2行が並び、`user_id`昇順('admin' < 'e1001')のため
    // `admin`が常に1行目になる。全ボタンをインデックスで拾うと`admin`の行を
    // 誤操作しうるため、`e1001`のテキストを含む行に絞ってボタンを取得する。
    const e1001Row = () => screen.getByText('e1001').closest('tr') as HTMLElement
    fireEvent.click(within(e1001Row()).getByRole('button', { name: '編集' }))
    fireEvent.change(screen.getByLabelText('氏名'), { target: { value: '山田次郎' } })
    fireEvent.click(screen.getByRole('button', { name: '更新' }))
    await screen.findByText('山田次郎')

    // 手順4: 無効化
    const originalConfirm = window.confirm
    window.confirm = () => true
    fireEvent.click(within(e1001Row()).getByRole('button', { name: '削除' }))
    await waitFor(() => {
      assert.ok(e1001Row().textContent?.includes('無効'))
    })
    window.confirm = originalConfirm
    cleanup()

    // 手順5
    const db = new DatabaseSync(server.dbPath, { readOnly: true })
    const row = db
      .prepare('SELECT name, password_hash, is_active FROM users WHERE user_id = ?')
      .get('e1001') as { name: string; password_hash: string; is_active: number } | undefined
    db.close()
    assert.ok(row)
    assert.equal(row?.name, '山田次郎')
    assert.equal(row?.is_active, 0)
    // パスワードが変更されていないこと(新しいパスワードを入力していないため)
    assert.ok(row?.password_hash.startsWith('scrypt$'))
  },
)
