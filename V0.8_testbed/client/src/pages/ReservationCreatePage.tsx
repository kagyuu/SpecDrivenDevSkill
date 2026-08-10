// U003-T5 (docs/P007-impl-direction/U003-reservation-core-and-calendar.md):
// S03予約作成画面 (docs/P002-frontend-spec.md 3.3節)。
//
// ★U004-T3改訂: バリデーションロジックを client/src/validation/reservationValidation.ts
// に切り出し、S04(ReservationDetailPage.tsx)と共有する形にした
// (U004-T3の実装してはいけないこと「バリデーションロジックの共通化が必要な場合は、
// 共通関数を新規ファイルに切り出して両画面から参照する形にすること」に対応。
// この画面自体の入力項目・挙動は変更していない)。
import { useEffect, useState, type FormEvent } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'

import {
  ReservationApiError,
  reservationApi,
  type ParticipantCandidate,
} from '../api/reservationApi'
import type { Room } from '../api/roomApi'
import {
  validateReservationForm,
  type ReservationFormErrors as FormErrors,
} from '../validation/reservationValidation'

const ALL_DAY_START = '09:00'
const ALL_DAY_END = '18:00'

interface FormState {
  roomId: string
  date: string
  startTime: string
  endTime: string
  allDay: boolean
  title: string
  participantUserIds: string[]
  attendeeCount: string
  notes: string
  meetingUrl: string
}

export function ReservationCreatePage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()

  const [rooms, setRooms] = useState<Room[]>([])
  const [candidates, setCandidates] = useState<ParticipantCandidate[]>([])
  const [form, setForm] = useState<FormState>({
    roomId: searchParams.get('room_id') ?? '',
    date: searchParams.get('date') ?? '',
    startTime: searchParams.get('start_time') ?? '',
    endTime: '',
    allDay: false,
    title: '',
    participantUserIds: [],
    attendeeCount: '',
    notes: '',
    meetingUrl: '',
  })
  const [errors, setErrors] = useState<FormErrors>({})
  const [conflictMessage, setConflictMessage] = useState<string | null>(null)

  useEffect(() => {
    reservationApi.listRooms().then(setRooms).catch(() => setRooms([]))
    reservationApi.listParticipantCandidates().then(setCandidates).catch(() => setCandidates([]))
  }, [])

  const selectedRoom = rooms.find((room) => String(room.room_id) === form.roomId)

  function toggleAllDay() {
    setForm((prev) => {
      const nextAllDay = !prev.allDay
      // docs/P002-frontend-spec.md 3.3節: チェックのたびに09:00/18:00で上書きする
      // (一度手動編集した値も再チェック時は保持しない、という単純化を仕様自身が
      // 明記している)。
      return nextAllDay
        ? { ...prev, allDay: true, startTime: ALL_DAY_START, endTime: ALL_DAY_END }
        : { ...prev, allDay: false }
    })
  }

  function toggleParticipant(employeeId: string) {
    setForm((prev) => ({
      ...prev,
      participantUserIds: prev.participantUserIds.includes(employeeId)
        ? prev.participantUserIds.filter((id) => id !== employeeId)
        : [...prev.participantUserIds, employeeId],
    }))
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setConflictMessage(null)
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
      await reservationApi.createReservation({
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
        setConflictMessage('選択した会議室・時間帯は既に予約されています')
        return
      }
      if (error instanceof ReservationApiError && error.fields) {
        setErrors(error.fields as FormErrors)
        return
      }
      setConflictMessage('予約の作成に失敗しました')
    }
  }

  function handleCancel() {
    navigate('/')
  }

  return (
    <div>
      <h1>予約作成</h1>
      {conflictMessage && <p role="alert">{conflictMessage}</p>}

      <form onSubmit={handleSubmit} aria-label="予約作成フォーム">
        <label htmlFor="reservation-room">会議室</label>
        <select
          id="reservation-room"
          value={form.roomId}
          onChange={(event) => setForm((prev) => ({ ...prev, roomId: event.target.value }))}
        >
          <option value="">選択してください</option>
          {rooms.map((room) => (
            <option key={room.room_id} value={room.room_id}>
              {room.name}
            </option>
          ))}
        </select>
        {errors.roomId && <p role="alert">{errors.roomId}</p>}

        <label htmlFor="reservation-date">日付</label>
        <input
          id="reservation-date"
          type="date"
          value={form.date}
          onChange={(event) => setForm((prev) => ({ ...prev, date: event.target.value }))}
        />
        {errors.date && <p role="alert">{errors.date}</p>}

        <label htmlFor="reservation-all-day">
          <input id="reservation-all-day" type="checkbox" checked={form.allDay} onChange={toggleAllDay} />
          終日
        </label>

        <label htmlFor="reservation-start-time">開始時刻</label>
        <input
          id="reservation-start-time"
          type="time"
          value={form.startTime}
          onChange={(event) => setForm((prev) => ({ ...prev, startTime: event.target.value }))}
        />
        {errors.startTime && <p role="alert">{errors.startTime}</p>}

        <label htmlFor="reservation-end-time">終了時刻</label>
        <input
          id="reservation-end-time"
          type="time"
          value={form.endTime}
          onChange={(event) => setForm((prev) => ({ ...prev, endTime: event.target.value }))}
        />
        {errors.endTime && <p role="alert">{errors.endTime}</p>}

        <label htmlFor="reservation-title">件名</label>
        <input
          id="reservation-title"
          value={form.title}
          onChange={(event) => setForm((prev) => ({ ...prev, title: event.target.value }))}
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

        <label htmlFor="reservation-attendee-count">参加予定人数</label>
        <input
          id="reservation-attendee-count"
          type="number"
          value={form.attendeeCount}
          onChange={(event) => setForm((prev) => ({ ...prev, attendeeCount: event.target.value }))}
        />
        {errors.attendeeCount && <p role="alert">{errors.attendeeCount}</p>}

        <label htmlFor="reservation-notes">備考</label>
        <textarea
          id="reservation-notes"
          value={form.notes}
          onChange={(event) => setForm((prev) => ({ ...prev, notes: event.target.value }))}
        />
        {errors.notes && <p role="alert">{errors.notes}</p>}

        <label htmlFor="reservation-meeting-url">オンライン会議URL</label>
        <input
          id="reservation-meeting-url"
          type="text"
          value={form.meetingUrl}
          onChange={(event) => setForm((prev) => ({ ...prev, meetingUrl: event.target.value }))}
        />
        {errors.meetingUrl && <p role="alert">{errors.meetingUrl}</p>}

        <button type="submit">登録</button>
        <button type="button" onClick={handleCancel}>
          キャンセル
        </button>
      </form>
    </div>
  )
}

export default ReservationCreatePage
