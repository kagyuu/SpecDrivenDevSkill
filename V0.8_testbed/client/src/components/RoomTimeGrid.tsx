// U003-T4 (docs/P007-impl-direction/U003-reservation-core-and-calendar.md):
// 会議室(列)×時間帯(行)のグリッド (docs/P002-frontend-spec.md 3.2節)。
// 行は30分刻み、表示範囲08:00〜20:00(★FIXME★ P001に営業時間・粒度の指定が無いため
// P002自身が仮定した値をそのまま使用。docs/P002-frontend-spec.md 3.2節参照)。
import type { Room } from '../api/roomApi'
import type { ReservationListItem } from '../api/reservationApi'

function buildTimeSlots(): string[] {
  const slots: string[] = []
  for (let minutes = 8 * 60; minutes < 20 * 60; minutes += 30) {
    const hour = String(Math.floor(minutes / 60)).padStart(2, '0')
    const minute = String(minutes % 60).padStart(2, '0')
    slots.push(`${hour}:${minute}`)
  }
  return slots
}

function addMinutes(time: string, minutesToAdd: number): string {
  const [hour, minute] = time.split(':').map(Number)
  const total = hour * 60 + minute + minutesToAdd
  return `${String(Math.floor(total / 60)).padStart(2, '0')}:${String(total % 60).padStart(2, '0')}`
}

function findReservation(
  reservations: ReservationListItem[],
  roomId: number,
  date: string,
  slotStart: string,
  slotEnd: string,
): ReservationListItem | undefined {
  const slotStartDt = `${date}T${slotStart}:00`
  const slotEndDt = `${date}T${slotEnd}:00`
  return reservations.find(
    (reservation) =>
      reservation.room_id === roomId &&
      reservation.start_datetime < slotEndDt &&
      reservation.end_datetime > slotStartDt,
  )
}

export interface RoomTimeGridProps {
  date: string
  rooms: Room[]
  reservations: ReservationListItem[]
  currentUserId: string
  onEmptyCellClick: (room: Room, time: string) => void
  onReservationClick: (reservation: ReservationListItem) => void
}

export function RoomTimeGrid({
  date,
  rooms,
  reservations,
  currentUserId,
  onEmptyCellClick,
  onReservationClick,
}: RoomTimeGridProps) {
  const slots = buildTimeSlots()

  return (
    <table>
      <thead>
        <tr>
          <th>時間帯</th>
          {rooms.map((room) => (
            <th key={room.room_id}>{room.name}</th>
          ))}
        </tr>
      </thead>
      <tbody>
        {slots.map((slotStart) => {
          const slotEnd = addMinutes(slotStart, 30)
          return (
            <tr key={slotStart}>
              <th scope="row">
                {slotStart}〜{slotEnd}
              </th>
              {rooms.map((room) => {
                const reservation = findReservation(reservations, room.room_id, date, slotStart, slotEnd)
                if (!reservation) {
                  return (
                    <td key={room.room_id}>
                      <button type="button" onClick={() => onEmptyCellClick(room, slotStart)}>
                        空き
                      </button>
                    </td>
                  )
                }
                const isMine = reservation.organizer_user_id === currentUserId
                return (
                  <td key={room.room_id} data-mine={isMine ? 'true' : 'false'}>
                    <button type="button" onClick={() => onReservationClick(reservation)}>
                      {reservation.organizer_name} / {reservation.title}
                    </button>
                  </td>
                )
              })}
            </tr>
          )
        })}
      </tbody>
    </table>
  )
}

export default RoomTimeGrid
