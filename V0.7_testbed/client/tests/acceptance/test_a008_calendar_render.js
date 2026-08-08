// A008 — カレンダー表示の性能(画面側 手順3・4)
// docs/P009-acceptance-direction/A008-calendar-performance.md
// API側の計測とN+1確認は server/tests/acceptance/test_a008_calendar_performance.py が行う。
import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { installDom } from '../helpers/dom-env.js';
import { startServer, makeFetch } from '../helpers/server.js';
import { jsonCaller, PASSWORD } from './support.js';
import * as api from '../../src/lib/api.js';
import { addDays, endOfWeek, startOfWeek, today } from '../../src/lib/datetime.js';

const ROOM_COUNT = 10;
const USER_COUNT = 10;
const RESERVATIONS = 200;

let server;
let httpFetch;
let env;
let s02;
let weekBase;

// 会議室10室・ユーザー10名・1週間分の予約200件を投入する(生成スクリプトを用いてよい)。
function generate(dbPath, weekStart) {
  const script = `
import sqlite3, sys
db_path, week_start = sys.argv[1], sys.argv[2]
sys.path.insert(0, sys.argv[3])
from datetime import date, timedelta
from meeting_room import security
conn = sqlite3.connect(db_path)
now = security.now_utc()
hashed = security.hash_password("${PASSWORD}")
for i in range(1, ${USER_COUNT} + 1):
    uid = "user%03d" % i
    if conn.execute("SELECT 1 FROM users WHERE user_id = ?", (uid,)).fetchone() is None:
        conn.execute(
            "INSERT INTO users(user_id, name, password_hash, role, is_active, created_at, updated_at)"
            " VALUES (?, ?, ?, 'general', 1, ?, ?)",
            (uid, "利用者%02d" % i, hashed, now, now),
        )
room_ids = []
for i in range(1, ${ROOM_COUNT} + 1):
    cur = conn.execute(
        "INSERT INTO rooms(name, capacity, equipment, description, is_active, created_at, updated_at)"
        " VALUES (?, 20, '', '', 1, ?, ?)",
        ("会議室%02d" % i, now, now),
    )
    room_ids.append(cur.lastrowid)
slots = [("09:00", "10:00"), ("11:00", "12:00"), ("13:00", "14:00"), ("15:00", "16:00")]
monday = date.fromisoformat(week_start)
count = 0
for day in range(5):
    reserved = (monday + timedelta(days=day)).isoformat()
    for room_id in room_ids:
        for start, end in slots:
            if count >= ${RESERVATIONS}:
                break
            conn.execute(
                "INSERT INTO reservations(room_id, user_id, reserved_date, start_time, end_time,"
                " title, attendee_count, note, created_at, updated_at)"
                " VALUES (?, ?, ?, ?, ?, ?, 5, '', ?, ?)",
                (room_id, "user%03d" % ((count % ${USER_COUNT}) + 1), reserved, start, end,
                 "会議%d" % count, now, now),
            )
            count += 1
conn.commit()
print(count)
`;
  const out = execFileSync(
    'python3',
    ['-c', script, dbPath, weekStart, new URL('../../../server/src', import.meta.url).pathname],
    { encoding: 'utf8' }
  );
  return Number(out.trim());
}

before(async () => {
  server = await startServer();
  httpFetch = makeFetch(server.baseUrl);
  const callJson = jsonCaller(httpFetch);
  // 予約は「翌週の月曜〜金曜」に置く(過去日にならないようにする)
  weekBase = addDays(startOfWeek(today()), 7);
  assert.equal(generate(server.dbPath, weekBase), RESERVATIONS);
  assert.equal(
    (await callJson('/api/auth/login', 'POST', { user_id: 'user001', password: PASSWORD })).status,
    200
  );
  env = installDom();
  api.runtime.fetch = httpFetch;
  api.runtime.navigate = (hash) => { globalThis.location.hash = hash; };
  s02 = await import('../../src/views/s02-calendar.js');
  // ウォームアップ(初回のimport・接続確立の影響を除く)
  s02.resetState();
  await s02.render({ date: weekBase }, env.app, env.header);
});

after(() => { if (server) server.stop(); });

function median(values) {
  const sorted = [...values].sort((a, b) => a - b);
  const mid = Math.floor(sorted.length / 2);
  return sorted.length % 2 ? sorted[mid] : (sorted[mid - 1] + sorted[mid]) / 2;
}

test('手順3・4: S02の描画とAPI取得を含む表示完了が3秒以内(中央値)', async () => {
  // 前提: 10室・200件のデータが投入されている
  const rooms = await (await httpFetch('/api/rooms')).json();
  assert.equal(rooms.rooms.length, ROOM_COUNT);
  const list = await (
    await httpFetch(`/api/reservations?date_from=${weekBase}&date_to=${endOfWeek(weekBase)}`)
  ).json();
  assert.equal(list.reservations.length, RESERVATIONS);

  // 手順3: 描画関数だけの所要時間を5回計測する
  const renderOnly = [];
  for (let i = 0; i < 5; i += 1) {
    const started = performance.now();
    s02.view(env.app);
    renderOnly.push(performance.now() - started);
  }

  // 手順4: API取得 + 描画(=画面表示完了までの目安)を5回計測する
  const total = [];
  for (let i = 0; i < 5; i += 1) {
    s02.resetState();
    const started = performance.now();
    const root = await s02.render({ date: weekBase }, env.app, env.header);
    total.push(performance.now() - started);
    assert.ok(root.querySelector('[data-role="grids"]'));
  }

  const renderMedian = median(renderOnly);
  const totalMedian = median(total);
  console.log(
    `[A008 計測(画面)] ${JSON.stringify({
      render_only_ms: renderOnly.map((v) => Math.round(v * 10) / 10),
      render_only_median_ms: Math.round(renderMedian * 10) / 10,
      total_ms: total.map((v) => Math.round(v * 10) / 10),
      total_median_ms: Math.round(totalMedian * 10) / 10,
      rooms: ROOM_COUNT,
      reservations: RESERVATIONS,
    })}`
  );
  assert.ok(totalMedian < 3000, `画面表示完了の中央値が3秒を超えた: ${totalMedian}ms`);
});
