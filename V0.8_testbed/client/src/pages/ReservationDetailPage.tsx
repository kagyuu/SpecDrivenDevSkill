// U004-T3 (docs/P007-impl-direction/U004-reservation-detail-and-mylist.md):
// S04予約詳細・編集画面 (docs/P002-frontend-spec.md 3.4節)。
import { useEffect, useState, type FormEvent } from 'react'
import { useNavigate, useParams } from 'react-router-dom'

import {
  ReservationApiError,
  reservationApi,
  type ParticipantCandidate,
  type ReservationDetail,
} from '../api/reservationApi'
import type { Room } from '../api/roomApi'
import {
  validateReservationForm,
  type ReservationFormErrors,
} from '../validation/reservationValidation'

interface FormState {
  roomId: string
  date: string
  startTime: string
  endTime: string
  title: string
  participantUserIds: string[]
  attendeeCount: string
  notes: string
  meetingUrl: string
}

function toFormState(reservation: ReservationDetail): FormState {
  return {
    roomId: String(reservation.room_id),
    date: reservation.date,
    startTime: reservation.start_time,
    endTime: reservation.end_time,
    title: reservation.title,
    participantUserIds: reservation.participants.map((participant) => participant.employee_id),
    attendeeCount: reservation.attendee_count === null ? '' : String(reservation.attendee_count),
    notes: reservation.notes ?? '',
    // CR-001 (docs/P901-cr-direction/CR-001.md, U004-T7).
    meetingUrl: reservation.meeting_url ?? '',
  }
}

export function ReservationDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const reservationId = Number(id)

  const [reservation, setReservation] = useState<ReservationDetail | null>(null)
  const [rooms, setRooms] = useState<Room[]>([])
  const [candidates, setCandidates] = useState<ParticipantCandidate[]>([])
  const [form, setForm] = useState<FormState | null>(null)
  const [errors, setErrors] = useState<ReservationFormErrors>({})
  const [message, setMessage] = useState<string | null>(null)
  const [loadError, setLoadError] = useState<string | null>(null)

  useEffect(() => {
    reservationApi
      .getReservation(reservationId)
      .then((detail) => {
        setReservation(detail)
        setForm(toFormState(detail))
      })
      .catch(() => setLoadError('予約情報の取得に失敗しました'))
    reservationApi.listRooms().then(setRooms).catch(() => setRooms([]))
    reservationApi.listParticipantCandidates().then(setCandidates).catch(() => setCandidates([]))
  }, [reservationId])

  if (loadError) {
    return <p role="alert">{loadError}</p>
  }
  if (!reservation || !form) {
    return null
  }

  // P202 F003 (docs/P202-fix-plan/F003-reservation-detail-inactive-room.md):
  // reservationApi.listRooms() only returns active rooms (docs/P002-frontend-spec.md
  // 3.6節: 無効化された会議室はS03のプルダウンから除外される). If the room
  // this reservation belongs to has since been deactivated, it would be
  // missing from `rooms` entirely, leaving the <select> with no matching
  // <option> and the room name invisible anywhere on screen - even though
  // docs/P002-frontend-spec.md 3.6節 requires existing reservations to keep
  // showing the room name. Splice in a placeholder entry built from the
  // reservation's own room_id/room_name when that happens, so the name is
  // always visible. Its capacity is unknown here (not part of the
  // reservation detail response), so it is left as +Infinity rather than 0
  // - guessing 0 would make validateReservationForm reject any
  // attendee_count as "over capacity", which is worse than not validating
  // it at all. In practice this placeholder can never actually be
  // submitted successfully anyway: the server's own update_reservation
  // re-validates that the room is active and rejects otherwise, so a user
  // must switch to an active room before saving.
  const roomOptions: Room[] = rooms.some((room) => room.room_id === reservation.room_id)
    ? rooms
    : [
        {
          room_id: reservation.room_id,
          name: reservation.room_name,
          capacity: Number.POSITIVE_INFINITY,
          equipment: [],
          description: null,
          is_active: false,
        },
        ...rooms,
      ]
  const selectedRoom = roomOptions.find((room) => String(room.room_id) === form.roomId)

  function toggleParticipant(employeeId: string) {
    setForm((prev) =>
      prev
        ? {
            ...prev,
            participantUserIds: prev.participantUserIds.includes(employeeId)
              ? prev.participantUserIds.filter((id) => id !== employeeId)
              : [...prev.participantUserIds, employeeId],
          }
        : prev,
    )
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!form) return
    setMessage(null)

    const validationErrors = validateReservationForm(
      {
        roomId: form.roomId,
        date: form.date,
        startTime: form.startTime,
        endTime: form.endTime,
        title: form.title,
        attendeeCount: form.attendeeCount,
        notes: form.notes,
        meetingUrl: form.meetingUrl,
      },
      selectedRoom?.capacity,
    )
    setErrors(validationErrors)
    if (Object.keys(validationErrors).length > 0) {
      return
    }

    try {
      await reservationApi.updateReservation(reservationId, {
        room_id: Number(form.roomId),
        date: form.date,
        start_time: form.startTime,
        end_time: form.endTime,
        title: form.title,
        participant_user_ids: form.participantUserIds,
        attendee_count: form.attendeeCount.trim() === '' ? null : Number(form.attendeeCount),
        notes: form.notes.trim() === '' ? null : form.notes,
        meeting_url: form.meetingUrl.trim() === '' ? null : form.meetingUrl,
      })
      navigate('/')
    } catch (error) {
      if (error instanceof ReservationApiError && error.status === 409) {
        setMessage('選択した会議室・時間帯は既に予約されています')
        return
      }
      if (error instanceof ReservationApiError && error.fields) {
        setErrors(error.fields as ReservationFormErrors)
        return
      }
      setMessage('予約の更新に失敗しました')
    }
  }

  async function handleCancelReservation() {
    if (!window.confirm('この予約を取り消しますか?')) {
      return
    }
    try {
      await reservationApi.cancelReservation(reservationId)
      navigate('/')
    } catch {
      setMessage('予約の取消に失敗しました')
    }
  }

  function handleDiscard() {
    navigate('/')
  }

  if (!reservation.editable) {
    return (
      <div>
        <h1>予約詳細</h1>
        <dl>
          <dt>会議室</dt>
          <dd>{reservation.room_name}</dd>
          <dt>日付</dt>
          <dd>{reservation.date}</dd>
          <dt>時間帯</dt>
          <dd>
            {reservation.start_time}〜{reservation.end_time}
          </dd>
          <dt>件名</dt>
          <dd>{reservation.title}</dd>
          <dt>オンライン会議URL</dt>
          <dd>
            {reservation.meeting_url ? (
              <a href={reservation.meeting_url} target="_blank" rel="noopener noreferrer">
                {reservation.meeting_url}
              </a>
            ) : (
              '(未設定)'
            )}
          </dd>
          <dt>予約者</dt>
          <dd>{reservation.organizer_name}</dd>
        </dl>
      </div>
    )
  }

  return (
    <div>
      <h1>予約詳細</h1>
      {message && <p role="alert">{message}</p>}

      <form onSubmit={handleSubmit} aria-label="予約編集フォーム">
        <label htmlFor="detail-room">会議室</label>
        <select
          id="detail-room"
          value={form.roomId}
          onChange={(event) => setForm((prev) => (prev ? { ...prev, roomId: event.target.value } : prev))}
        >
          {roomOptions.map((room) => (
            <option key={room.room_id} value={room.room_id}>
              {room.name}
            </option>
          ))}
        </select>
        {errors.roomId && <p role="alert">{errors.roomId}</p>}

        <label htmlFor="detail-date">日付</label>
        <input
          id="detail-date"
          type="date"
          value={form.date}
          onChange={(event) => setForm((prev) => (prev ? { ...prev, date: event.target.value } : prev))}
        />
        {errors.date && <p role="alert">{errors.date}</p>}

        <label htmlFor="detail-start-time">開始時刻</label>
        <input
          id="detail-start-time"
          type="time"
          value={form.startTime}
          onChange={(event) => setForm((prev) => (prev ? { ...prev, startTime: event.target.value } : prev))}
        />
        {errors.startTime && <p role="alert">{errors.startTime}</p>}

        <label htmlFor="detail-end-time">終了時刻</label>
        <input
          id="detail-end-time"
          type="time"
          value={form.endTime}
          onChange={(event) => setForm((prev) => (prev ? { ...prev, endTime: event.target.value } : prev))}
        />
        {errors.endTime && <p role="alert">{errors.endTime}</p>}

        <label htmlFor="detail-title">件名</label>
        <input
          id="detail-title"
          value={form.title}
          onChange={(event) => setForm((prev) => (prev ? { ...prev, title: event.target.value } : prev))}
        />
        {errors.title && <p role="alert">{errors.title}</p>}

        <fieldset>
          <legend>参加者</legend>
          {candidates.map((candidate) => (
            <label key={candidate.employee_id}>
              <input
                type="checkbox"
                checked={form.participantUserIds.includes(candidate.employee_id)}
                onChange={() => toggleParticipant(candidate.employee_id)}
              />
              {candidate.name}
            </label>
          ))}
        </fieldset>

        <label htmlFor="detail-attendee-count">参加予定人数</label>
        <input
          id="detail-attendee-count"
          type="number"
          value={form.attendeeCount}
          onChange={(event) =>
            setForm((prev) => (prev ? { ...prev, attendeeCount: event.target.value } : prev))
          }
        />
        {errors.attendeeCount && <p role="alert">{errors.attendeeCount}</p>}

        <label htmlFor="detail-notes">備考</label>
        <textarea
          id="detail-notes"
          value={form.notes}
          onChange={(event) => setForm((prev) => (prev ? { ...prev, notes: event.target.value } : prev))}
        />
        {errors.notes && <p role="alert">{errors.notes}</p>}

        <label htmlFor="detail-meeting-url">オンライン会議URL</label>
        <input
          id="detail-meeting-url"
          type="text"
          value={form.meetingUrl}
          onChange={(event) =>
            setForm((prev) => (prev ? { ...prev, meetingUrl: event.target.value } : prev))
          }
        />
        {errors.meetingUrl && <p role="alert">{errors.meetingUrl}</p>}

        <button type="submit">更新</button>
        <button type="button" onClick={handleDiscard}>
          キャンセル
        </button>
        <button type="button" onClick={handleCancelReservation}>
          取消
        </button>
      </form>
    </div>
  )
}

export default ReservationDetailPage
