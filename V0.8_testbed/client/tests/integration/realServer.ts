// Shared helper for P008/P103 integration tests that must exercise a real,
// running server rather than a mocked one - e.g. T002's own 【事前準備】:
// "テスト用サーバーを起動し...APIをモックせず実サーバーに対して呼び出す結合
// テストとして実装する". Every tests/integration/*.test.tsx file imports
// this instead of mocking authApi/roomApi/etc.
//
// Node's global fetch (undici) does two things a real browser does
// automatically that these tests still need:
//   1. Resolve the app's relative "/api/..." URLs against an origin.
//   2. Store/replay cookies across requests (a "cookie jar") so
//      `credentials: 'include'` actually keeps a session logged in across
//      calls, the way it would in a browser.
// This module patches globalThis.fetch to add both for the lifetime of a
// started server, and spawns/tears down a real `uvicorn` process (the same
// server/app/main.py used in production) against a fresh temp SQLite DB per
// test file - so these tests hit the real FastAPI app, Service layer,
// Repository layer, and DB, not test doubles.
import { spawn, spawnSync, type ChildProcess } from 'node:child_process'
import { unlink } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const SERVER_DIR = path.resolve(__dirname, '../../../server')
const PYTHON_EXE = path.join(SERVER_DIR, '.venv', 'Scripts', 'python.exe')

type CookieJar = Map<string, string>

function applyCookieJar(jar: CookieJar, init: RequestInit): RequestInit {
  if (jar.size === 0) return init
  const cookieHeader = [...jar.entries()].map(([name, value]) => `${name}=${value}`).join('; ')
  const headers = new Headers(init.headers)
  headers.set('cookie', cookieHeader)
  return { ...init, headers }
}

function captureCookies(jar: CookieJar, response: Response): void {
  const headersWithGetSetCookie = response.headers as Headers & { getSetCookie?: () => string[] }
  const setCookieValues = headersWithGetSetCookie.getSetCookie?.() ?? []
  for (const raw of setCookieValues) {
    const [pair, ...attributes] = raw.split(';')
    const eqIndex = pair.indexOf('=')
    if (eqIndex === -1) continue
    const name = pair.slice(0, eqIndex).trim()
    const value = pair.slice(eqIndex + 1).trim()
    const isCleared = attributes.some((attr) => attr.trim().toLowerCase() === 'max-age=0') || value === ''
    if (isCleared) {
      jar.delete(name)
    } else {
      jar.set(name, value)
    }
  }
}

export interface RealServer {
  baseUrl: string
  /** Absolute path to the temp SQLite file this server instance uses -
   * tests that need to "SQLiteを直接クエリし" (per several T0NN specs) open
   * this directly with node:sqlite's DatabaseSync. */
  dbPath: string
  /** Drops all stored cookies (simulates a fresh, logged-out browser tab). */
  resetSession: () => void
  stop: () => Promise<void>
}

function killProcessTree(child: ChildProcess): void {
  // `python -m uvicorn` spawns a SECOND python.exe as an actual child
  // process on Windows (the launcher re-execs). child.kill() only signals
  // the direct child (the launcher) - the uvicorn worker underneath keeps
  // running, still holding the port and the sqlite file open, and leaks
  // across test runs. `taskkill /t` kills the whole tree instead.
  if (process.platform === 'win32' && child.pid !== undefined) {
    spawnSync('taskkill', ['/pid', String(child.pid), '/t', '/f'])
  } else {
    child.kill()
  }
}

async function waitUntilReady(baseUrl: string, originalFetch: typeof fetch): Promise<void> {
  const deadline = Date.now() + 20_000
  let lastError: unknown
  while (Date.now() < deadline) {
    try {
      const response = await originalFetch(`${baseUrl}/health`)
      if (response.ok) return
    } catch (error) {
      lastError = error
    }
    await new Promise((resolve) => setTimeout(resolve, 200))
  }
  throw new Error(`server did not become ready at ${baseUrl}: ${String(lastError)}`)
}

export async function startRealServer(): Promise<RealServer> {
  const port = 9100 + Math.floor(Math.random() * 2000)
  const baseUrl = `http://127.0.0.1:${port}`
  const dbPath = path.join(SERVER_DIR, `.tmp_integration_${port}_${process.pid}.db`)

  const child: ChildProcess = spawn(
    PYTHON_EXE,
    ['-m', 'uvicorn', 'app.main:app', '--port', String(port)],
    {
      cwd: SERVER_DIR,
      env: { ...process.env, DATABASE_PATH: dbPath, COOKIE_SECURE: 'false' },
      stdio: ['ignore', 'pipe', 'pipe'],
    },
  )
  if (process.env.DEBUG_REAL_SERVER) {
    child.stdout?.on('data', (chunk) => process.stdout.write(`[server ${port}] ${chunk}`))
    child.stderr?.on('data', (chunk) => process.stderr.write(`[server ${port}] ${chunk}`))
  }

  const originalFetch = globalThis.fetch
  const jar: CookieJar = new Map()

  globalThis.fetch = (async (input: RequestInfo | URL, init: RequestInit = {}) => {
    const url =
      typeof input === 'string' && input.startsWith('/') ? `${baseUrl}${input}` : input
    const response = await originalFetch(url as RequestInfo, applyCookieJar(jar, init))
    captureCookies(jar, response)
    return response
  }) as typeof fetch

  try {
    await waitUntilReady(baseUrl, originalFetch)
  } catch (error) {
    globalThis.fetch = originalFetch
    killProcessTree(child)
    throw error
  }

  return {
    baseUrl,
    dbPath,
    resetSession: () => jar.clear(),
    stop: async () => {
      globalThis.fetch = originalFetch
      const exited = new Promise<void>((resolve) => child.once('exit', () => resolve()))
      killProcessTree(child)
      // Windows holds the sqlite file open until the process has actually
      // exited (not just been signaled) - unlinking immediately after
      // kill() intermittently fails/no-ops with the file still present.
      await Promise.race([exited, new Promise((resolve) => setTimeout(resolve, 3000))])
      for (let attempt = 0; attempt < 5; attempt += 1) {
        try {
          await unlink(dbPath)
          break
        } catch {
          await new Promise((resolve) => setTimeout(resolve, 200))
        }
      }
    },
  }
}
