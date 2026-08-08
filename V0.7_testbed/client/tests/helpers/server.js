// 結合テスト用: 実際のサーバープロセス(uvicorn)を起動し、Cookieを保持する fetch を提供する。
// P008 T003・T010 の「実サーバーに向ける方を優先する」に従う。

import { spawn } from 'node:child_process';
import { mkdtempSync, rmSync } from 'node:fs';
import net from 'node:net';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HELPERS_DIR = path.dirname(fileURLToPath(import.meta.url));
const CLIENT_DIR = path.resolve(HELPERS_DIR, '..', '..');
const SERVER_DIR = path.resolve(CLIENT_DIR, '..', 'server');

function freePort() {
  return new Promise((resolve, reject) => {
    const server = net.createServer();
    server.on('error', reject);
    server.listen(0, '127.0.0.1', () => {
      const { port } = server.address();
      server.close(() => resolve(port));
    });
  });
}

async function waitReady(baseUrl, child, timeoutMs = 20000) {
  const deadline = Date.now() + timeoutMs;
  let lastError = null;
  while (Date.now() < deadline) {
    if (child.exitCode !== null) throw new Error(`サーバーが終了した (code=${child.exitCode})`);
    try {
      const res = await fetch(`${baseUrl}/`);
      if (res.status === 200) return;
    } catch (e) {
      lastError = e;
    }
    await new Promise((r) => setTimeout(r, 200));
  }
  throw new Error(`サーバーの起動待ちがタイムアウトした: ${lastError}`);
}

export async function startServer() {
  const dir = mkdtempSync(path.join(tmpdir(), 'meeting-room-it-'));
  const dbPath = path.join(dir, 'app.db');
  const port = await freePort();
  const child = spawn(
    'python3',
    ['-m', 'uvicorn', 'meeting_room.main:app', '--port', String(port), '--log-level', 'warning'],
    {
      cwd: SERVER_DIR,
      env: {
        ...process.env,
        PYTHONPATH: path.join(SERVER_DIR, 'src'),
        DB_PATH: dbPath,
        INITIAL_ADMIN_ID: 'admin001',
        INITIAL_ADMIN_PASSWORD: 'Passw0rd!23',
      },
      stdio: ['ignore', 'pipe', 'pipe'],
    }
  );
  const logs = [];
  child.stdout.on('data', (d) => logs.push(String(d)));
  child.stderr.on('data', (d) => logs.push(String(d)));
  const baseUrl = `http://127.0.0.1:${port}`;
  await waitReady(baseUrl, child);
  return {
    baseUrl,
    dbPath,
    logs,
    stop() {
      child.kill('SIGTERM');
      rmSync(dir, { recursive: true, force: true });
    },
  };
}

// ブラウザの Cookie 保持を模した fetch(サーバーは HttpOnly Cookie を返す)。
export function makeFetch(baseUrl) {
  let jar = '';
  const wrapped = async (target, options = {}) => {
    const headers = { ...(options.headers || {}) };
    if (jar) headers.Cookie = jar;
    const res = await fetch(`${baseUrl}${target}`, { ...options, headers });
    const setCookies = typeof res.headers.getSetCookie === 'function' ? res.headers.getSetCookie() : [];
    for (const cookie of setCookies) {
      const [pair] = cookie.split(';');
      const index = pair.indexOf('=');
      const name = pair.slice(0, index);
      const value = pair.slice(index + 1);
      jar = value === '' ? '' : `${name}=${value}`;
    }
    return res;
  };
  wrapped.clearCookies = () => { jar = ''; };
  return wrapped;
}
