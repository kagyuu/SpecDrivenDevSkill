// U003-T4 (docs/P007-impl-direction/U003-reservation-core-and-calendar.md):
// fetch wrappers for GET /api/reservations and (re-exported) GET /api/rooms.
// U003-T5 adds createReservation/listParticipantCandidates. U004-T2 adds
// getReservation/updateReservation/cancelReservation. U004-T4 adds
// listMyReservations - all to this same file, per each task's own
// 作成・編集対象ファイル.
import { roomApi, type Room } from './roomApi'

export interface ReservationListItem {
  reservation_id: number
  room_id: number
  room_name: string
  organizer_user_id: string
  organizer_name: string
  title: string
  start_datetime: string
  end_datetime: string
}

export interface ReservationDetail {
  reservation_id: number
  room_id: number
  room_name: string
  organizer_user_id: string
  organizer_name: string
  date: string
  start_time: string
  end_time: string
  title: string
  participants: { employee_id: string; name: string }[]
  attendee_count: number | null
  notes: string | null
  // CR-001 (docs/P901-cr-direction/CR-001.md, U003-T8/U004-T7).
  meeting_url: string | null
  editable: boolean
}

export interface ReservationCreateInput {
  room_id: number
  date: string
  start_time: string
  end_time: string
  title: string
  participant_user_ids: string[]
  attendee_count: number | null
  notes: string | null
  // CR-001 (docs/P901-cr-direction/CR-001.md, U003-T8/U004-T7).
  meeting_url: string | null
}

export interface ParticipantCandidate {
  employee_id: string
  name: string
}

export interface MyReservationListItem {
  reservation_id: number
  room_id: number
  room_name: string
  date: string
  start_time: string
  end_time: string
  title: string
}

export type MyReservationsPeriod = 'upcoming' | 'past' | 'all'

export interface ReservationApiErrorBody {
  code: string
  message: string
  fields?: Record<string, string>
}

// Duplicated small error class (see roomApi.ts's own comment for why: no
// shared file is in this task's scope).
export class ReservationApiError extends Error {
  status: number
  code: string
  fields?: Record<string, string>

  constructor(status: number, body: ReservationApiErrorBody) {
    super(body.message)
    this.status = status
    this.code = body.code
    this.fields = body.fields
  }
}

async function throwApiError(response: Response): Promise<never> {
  const parsed = await response.json().catch(() => null)
  const body: ReservationApiErrorBody = parsed?.error ?? {
    code: 'UNKNOWN',
    message: '通信エラーが発生しました',
  }
  throw new ReservationApiError(response.status, body)
}

async function listReservations(
  dateFrom: string,
  dateTo: string,
  roomIds?: number[],
): Promise<ReservationListItem[]> {
  const params = new URLSearchParams({ date_from: dateFrom, date_to: dateTo })
  for (const roomId of roomIds ?? []) {
    params.append('room_id', String(roomId))
  }
  const response = await fetch(`/api/reservations?${params.toString()}`, {
    credentials: 'include',
  })
  if (!response.ok) {
    return throwApiError(response)
  }
  return response.json()
}

async function listRooms(): Promise<Room[]> {
  // Thin re-export of roomApi.listRooms (general users never pass
  // include_inactive - docs/P002-frontend-spec.md 3.2節's calendar filter
  // only ever lists active rooms).
  return roomApi.listRooms(false)
}

async function createReservation(input: ReservationCreateInput): Promise<ReservationDetail> {
  const response = await fetch('/api/reservations', {
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

async function listParticipantCandidates(): Promise<ParticipantCandidate[]> {
  const response = await fetch('/api/users/directory', { credentials: 'include' })
  if (!response.ok) {
    return throwApiError(response)
  }
  return response.json()
}

async function getReservation(reservationId: number): Promise<ReservationDetail> {
  const response = await fetch(`/api/reservations/${reservationId}`, { credentials: 'include' })
  if (!response.ok) {
    return throwApiError(response)
  }
  return response.json()
}

async function updateReservation(
  reservationId: number,
  input: ReservationCreateInput,
): Promise<ReservationDetail> {
  const response = await fetch(`/api/reservations/${reservationId}`, {
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

async function cancelReservation(reservationId: number): Promise<void> {
  const response = await fetch(`/api/reservations/${reservationId}`, {
    method: 'DELETE',
    credentials: 'include',
  })
  if (!response.ok) {
    return throwApiError(response)
  }
}

async function listMyReservations(
  period: MyReservationsPeriod = 'upcoming',
): Promise<MyReservationListItem[]> {
  const response = await fetch(`/api/reservations/mine?period=${period}`, {
    credentials: 'include',
  })
  if (!response.ok) {
    return throwApiError(response)
  }
  return response.json()
}

export const reservationApi = {
  listReservations,
  listRooms,
  createReservation,
  listParticipantCandidates,
  getReservation,
  updateReservation,
  cancelReservation,
  listMyReservations,
}
