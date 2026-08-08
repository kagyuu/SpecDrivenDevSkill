// A006 — 認証セッションのライフサイクル(画面側 手順5)
// docs/P009-acceptance-direction/A006-session-lifecycle.md
// API側(手順1〜4・6〜8)は server/tests/acceptance/test_a006_session_lifecycle.py が確認する。
import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { installDom } from '../helpers/dom-env.js';
import { startWithBaseData, PASSWORD } from './support.js';
import * as api from '../../src/lib/api.js';
import { today } from '../../src/lib/datetime.js';

let server;
let httpFetch;
let env;
let s01;
let s02;

function deleteAllSessions(dbPath) {
  const script = `
import sqlite3, sys
conn = sqlite3.connect(sys.argv[1])
conn.execute("DELETE FROM sessions")
conn.commit()
print(conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0])
`;
  return execFileSync('python3', ['-c', script, dbPath], { encoding: 'utf8' }).trim();
}

before(async () => {
  let callJson;
  ({ server, httpFetch, callJson } = await startWithBaseData());
  assert.equal(
    (await callJson('/api/auth/login', 'POST', { user_id: 'user001', password: PASSWORD })).status,
    200
  );
  env = installDom();
  api.runtime.fetch = httpFetch;
  api.runtime.navigate = (hash) => { globalThis.location.hash = hash; };
  s01 = await import('../../src/views/s01-login.js');
  s02 = await import('../../src/views/s02-calendar.js');
  s02.resetState();
  s02.takeFlash();
});

after(() => { if (server) server.stop(); });

test('手順5: S02表示中にセッションが消えると #/login へ遷移しセッション切れメッセージが出る', async () => {
  const root = await s02.render({ date: today() }, env.app, env.header);
  assert.ok(root.querySelector('[data-role="grids"]'), 'S02が描画されている');
  globalThis.location.hash = '#/calendar';

  // セッションを削除する(サーバー再起動なし・Cookieはそのまま残る)
  assert.equal(deleteAllSessions(server.dbPath), '0');

  // 画面操作(翌週ボタン)を行うと 401 になり、共通処理でS01へ戻される(P002 2.3 / 2.4)
  let thrown = null;
  try {
    await root.querySelector('[data-action="next-week"]').click();
  } catch (error) {
    thrown = error; // api.js は遷移後にエラーを再送出する
  }
  assert.ok(thrown, '401 が呼び出し側へ伝播する');
  assert.equal(thrown.status, 401);
  assert.equal(thrown.code, 'UNAUTHENTICATED');
  assert.equal(globalThis.location.hash, '#/login', 'S01へ遷移する');

  // S01を描画するとセッション切れメッセージが表示される
  const form = s01.render({}, env.app, env.header);
  assert.equal(
    form.querySelector('[data-top-message]').textContent,
    'セッションの有効期限が切れました。再度ログインしてください。'
  );
  assert.equal(env.header.textContent, '', 'S01では共通ヘッダーを描画しない');
});
