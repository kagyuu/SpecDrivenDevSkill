// U003-T4 (docs/P007-impl-direction/U003-reservation-core-and-calendar.md):
// S02予約カレンダー画面(トップ) (docs/P002-frontend-spec.md 3.2節)。
// ★U005-T4改訂: 独自の<header>マークアップをHeaderコンポーネントに置き換えた
// (置き換え以外の変更はしていない)。
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { authApi, type CurrentUser } from '../api/authApi'
import { reservationApi, type ReservationListItem } from '../api/reservationApi'
import type { Room } from '../api/roomApi'
import { Header } from '../components/Header'
import { RoomTimeGrid } from '../components/RoomTimeGrid'

function todayIsoDate(): string {
  return new Date().toISOString().slice(0, 10)
}

// P202 F002 (docs/P202-fix-plan/F002-calendar-adddays-timezone.md): the
// previous implementation built `new Date(`${isoDate}T00:00:00`)`, which
// JavaScript parses as LOCAL midnight, then re-serialized via
// `toISOString()` (UTC). In timezones ahead of UTC (e.g. Asia/Tokyo,
// UTC+9), depending on the time of day this could round-trip back to the
// SAME calendar date, making "前へ"/"次へ" silently no-ops
// (docs/test-records/20260809-1500-test-record.md T006). Building the Date
// via Date.UTC(...) and advancing with setUTCDate keeps every step in UTC,
// so the local timezone never enters the calculation.
function addDays(isoDate: string, days: number): string {
  const [year, month, day] = isoDate.split('-').map(Number)
  const utcDate = new Date(Date.UTC(year, month - 1, day))
  utcDate.setUTCDate(utcDate.getUTCDate() + days)
  return utcDate.toISOString().slice(0, 10)
}

export function CalendarPage() {
  const navigate = useNavigate()
  const [user, setUser] = useState<CurrentUser | null>(null)
  const [date, setDate] = useState(todayIsoDate())
  const [rooms, setRooms] = useState<Room[]>([])
  const [selectedRoomIds, setSelectedRoomIds] = useState<number[]>([])
  const [reservations, setReservations] = useState<ReservationListItem[]>([])
  const [error, setError] = useState<string | null>(null)
  const [tooltip, setTooltip] = useState<{ title: string; organizerName: string } | null>(null)

  useEffect(() => {
    authApi.getMe().then(setUser).catch(() => navigate('/login', { replace: true }))
  }, [navigate])

  useEffect(() => {
    reservationApi
      .listRooms()
      .then(setRooms)
      .catch(() => setError('会議室一覧の取得に失敗しました'))
  }, [])

  useEffect(() => {
    reservationApi
      .listReservations(date, date, selectedRoomIds.length > 0 ? selectedRoomIds : undefined)
      .then((items) => {
        setReservations(items)
        setError(null)
      })
      .catch(() => setError('予約一覧の取得に失敗しました'))
  }, [date, selectedRoomIds])

  function toggleRoomFilter(roomId: number) {
    setSelectedRoomIds((prev) =>
      prev.includes(roomId) ? prev.filter((id) => id !== roomId) : [...prev, roomId],
    )
  }

  function handleEmptyCellClick(room: Room, time: string) {
    const params = new URLSearchParams({ room_id: String(room.room_id), date, start_time: time })
    navigate(`/reservations/new?${params.toString()}`)
  }

  function handleReservationClick(reservation: ReservationListItem) {
    const isRelated = user?.role === 'admin' || reservation.organizer_user_id === user?.employee_id
    // ★FIXME★ docs/P002-frontend-spec.md 3.2節は「自分が予約者、または参加者に
    // なっている予約」をS04へ遷移可能としているが、この画面が呼ぶGET /api/reservations
    // (4.6節)のレスポンスには参加者一覧が含まれない(3.6節「参加予定人数は表示しない」と
    // 同じ理由でレスポンスを軽量化しているため)。そのため「参加者かどうか」はここでは
    // 判定できず、暫定的に「予約者本人または管理者」のみを遷移対象としている。
    if (isRelated) {
      navigate(`/reservations/${reservation.reservation_id}`)
      return
    }
    setTooltip({ title: reservation.title, organizerName: reservation.organizer_name })
  }

  return (
    <div>
      <Header currentScreen="S02" />

      <h1>予約カレンダー</h1>
      {error && <p role="alert">{error}</p>}

      <div>
        <button type="button" onClick={() => setDate((prev) => addDays(prev, -1))}>
          前へ
        </button>
        <span>{date}</span>
        <button type="button" onClick={() => setDate((prev) => addDays(prev, 1))}>
          次へ
        </button>
      </div>

      <fieldset>
        <legend>会議室フィルタ</legend>
        {rooms.map((room) => (
          <label key={room.room_id}>
            <input
              type="checkbox"
              checked={selectedRoomIds.includes(room.room_id)}
              onChange={() => toggleRoomFilter(room.room_id)}
            />
            {room.name}
          </label>
        ))}
      </fieldset>

      {tooltip && (
        <p role="status">
          {tooltip.title} / {tooltip.organizerName}
        </p>
      )}

      <RoomTimeGrid
        date={date}
        rooms={rooms}
        reservations={reservations}
        currentUserId={user?.employee_id ?? ''}
        onEmptyCellClick={handleEmptyCellClick}
        onReservationClick={handleReservationClick}
      />
    </div>
  )
}

export default CalendarPage
