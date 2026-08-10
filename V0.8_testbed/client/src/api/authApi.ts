// U001-T5 (docs/P007-impl-direction/U001-foundation-and-auth.md): fetch
// wrappers for POST /api/auth/login, POST /api/auth/logout, GET /api/me
// (docs/P002-frontend-spec.md 4.1〜4.3節). `credentials: 'include'` so the
// HttpOnly session_id Cookie (docs/ADR.md ADR-003) is sent/received.

export type Role = 'general' | 'admin'

export interface CurrentUser {
  employee_id: string
  name: string
  role: Role
}

export interface ApiErrorBody {
  code: string
  message: string
  fields?: Record<string, string>
}

export class AuthApiError extends Error {
  status: number
  code: string
  fields?: Record<string, string>

  constructor(status: number, body: ApiErrorBody) {
    super(body.message)
    this.status = status
    this.code = body.code
    this.fields = body.fields
  }
}

async function throwApiError(response: Response): Promise<never> {
  const parsed = await response.json().catch(() => null)
  const body: ApiErrorBody = parsed?.error ?? {
    code: 'UNKNOWN',
    message: '通信エラーが発生しました',
  }
  throw new AuthApiError(response.status, body)
}

async function login(employeeId: string, password: string): Promise<CurrentUser> {
  const response = await fetch('/api/auth/login', {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ employee_id: employeeId, password }),
  })
  if (!response.ok) {
    return throwApiError(response)
  }
  return response.json()
}

async function logout(): Promise<void> {
  const response = await fetch('/api/auth/logout', {
    method: 'POST',
    credentials: 'include',
  })
  if (!response.ok) {
    return throwApiError(response)
  }
}

async function getMe(): Promise<CurrentUser> {
  const response = await fetch('/api/me', {
    method: 'GET',
    credentials: 'include',
  })
  if (!response.ok) {
    return throwApiError(response)
  }
  return response.json()
}

// Exported as a single mutable object (rather than three separate named
// function exports) so tests/LoginPage.test.tsx can monkeypatch individual
// methods (e.g. `authApi.login = mock.fn(...)`) directly - reassigning a
// property on an object is allowed even though ESM named-export bindings
// themselves are read-only from the importer's side. This avoids needing
// Node's --experimental-test-module-mocks flag, which
// docs/P007-impl-direction/U001-foundation-and-auth.md U001-T5's own
// 【実行コマンド】(`node --import tsx --test tests/LoginPage.test.tsx`) does
// not include.
export const authApi = { login, logout, getMe }
