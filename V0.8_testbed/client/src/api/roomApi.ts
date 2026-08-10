// U002-T3 (docs/P007-impl-direction/U002-room-management.md): fetch
// wrappers for GET/POST/PUT/DELETE /api/rooms (docs/P002-frontend-spec.md
// 4.4〜4.5.2節).

export interface Room {
  room_id: number
  name: string
  capacity: number
  equipment: string[]
  description: string | null
  is_active: boolean
}

export interface RoomInput {
  name: string
  capacity: number
  equipment: string[]
  description: string | null
}

export interface RoomApiErrorBody {
  code: string
  message: string
  fields?: Record<string, string>
}

// Duplicated from client/src/api/authApi.ts's AuthApiError rather than
// factored into a shared module: U002-T3's own 作成・編集対象ファイル list
// does not include a new shared file, and editing authApi.ts is out of this
// task's scope (U001-T5's file).
export class RoomApiError extends Error {
  status: number
  code: string
  fields?: Record<string, string>

  constructor(status: number, body: RoomApiErrorBody) {
    super(body.message)
    this.status = status
    this.code = body.code
    this.fields = body.fields
  }
}

async function throwApiError(response: Response): Promise<never> {
  const parsed = await response.json().catch(() => null)
  const body: RoomApiErrorBody = parsed?.error ?? {
    code: 'UNKNOWN',
    message: '通信エラーが発生しました',
  }
  throw new RoomApiError(response.status, body)
}

async function listRooms(includeInactive = false): Promise<Room[]> {
  const query = includeInactive ? '?include_inactive=true' : ''
  const response = await fetch(`/api/rooms${query}`, { credentials: 'include' })
  if (!response.ok) {
    return throwApiError(response)
  }
  return response.json()
}

async function createRoom(input: RoomInput): Promise<Room> {
  const response = await fetch('/api/rooms', {
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

async function updateRoom(roomId: number, input: RoomInput & { is_active: boolean }): Promise<Room> {
  const response = await fetch(`/api/rooms/${roomId}`, {
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

async function deleteRoom(roomId: number): Promise<{ room_id: number; is_active: boolean }> {
  const response = await fetch(`/api/rooms/${roomId}`, {
    method: 'DELETE',
    credentials: 'include',
  })
  if (!response.ok) {
    return throwApiError(response)
  }
  return response.json()
}

// Mutable exports object (see authApi.ts's own comment for why): lets tests
// monkeypatch individual methods without Node's
// --experimental-test-module-mocks flag.
export const roomApi = { listRooms, createRoom, updateRoom, deleteRoom }
