// U005-T3 (docs/P007-impl-direction/U005-user-management-and-hardening.md):
// fetch wrappers for GET/POST/PUT/DELETE /api/users (docs/P002-frontend-spec.md
// 4.10〜4.11.2節, admin-only).

export type Role = 'general' | 'admin'

export interface ManagedUser {
  employee_id: string
  name: string
  role: Role
  is_active: boolean
}

export interface UserCreateInput {
  employee_id: string
  name: string
  password: string
  role: Role
}

export interface UserUpdateInput {
  name: string
  password: string | null
  role: Role
  is_active: boolean
}

export interface UserApiErrorBody {
  code: string
  message: string
  fields?: Record<string, string>
}

// Duplicated small error class (see roomApi.ts's own comment for why: no
// shared file is in this task's scope).
export class UserApiError extends Error {
  status: number
  code: string
  fields?: Record<string, string>

  constructor(status: number, body: UserApiErrorBody) {
    super(body.message)
    this.status = status
    this.code = body.code
    this.fields = body.fields
  }
}

async function throwApiError(response: Response): Promise<never> {
  const parsed = await response.json().catch(() => null)
  const body: UserApiErrorBody = parsed?.error ?? {
    code: 'UNKNOWN',
    message: '通信エラーが発生しました',
  }
  throw new UserApiError(response.status, body)
}

async function listUsers(includeInactive = false): Promise<ManagedUser[]> {
  const query = includeInactive ? '?include_inactive=true' : ''
  const response = await fetch(`/api/users${query}`, { credentials: 'include' })
  if (!response.ok) {
    return throwApiError(response)
  }
  return response.json()
}

async function createUser(input: UserCreateInput): Promise<ManagedUser> {
  const response = await fetch('/api/users', {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  })
  if (!response.ok) {
    return throwApiError(response)
  }
  return response.json()
}

async function updateUser(employeeId: string, input: UserUpdateInput): Promise<ManagedUser> {
  const response = await fetch(`/api/users/${employeeId}`, {
    method: 'PUT',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  })
  if (!response.ok) {
    return throwApiError(response)
  }
  return response.json()
}

async function deleteUser(employeeId: string): Promise<{ employee_id: string; is_active: boolean }> {
  const response = await fetch(`/api/users/${employeeId}`, {
    method: 'DELETE',
    credentials: 'include',
  })
  if (!response.ok) {
    return throwApiError(response)
  }
  return response.json()
}

export const userApi = { listUsers, createUser, updateUser, deleteUser }
