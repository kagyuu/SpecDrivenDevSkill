// S02 予約カレンダー画面の中核グリッド。docs/P002-frontend-spec.md §3 S02。
import type { Reservation } from "../api/reservations";
import type { Room } from "../api/rooms";

interface Props {
  rooms: Room[];
  reservations: Reservation[];
  date: string; // "YYYY-MM-DD"、このグリッドが表示する1日分
  currentUserId: number;
  onCellClick: (room: Room, reservation: Reservation | null) => void;
}

// 09:00-18:00, 30分刻み(既定表示範囲)。docs/P002-frontend-spec.md §3 S02。
const TIME_SLOTS = Array.from({ length: 18 }, (_, i) => {
  const totalMinutes = 9 * 60 + i * 30;
  const h = String(Math.floor(totalMinutes / 60)).padStart(2, "0");
  const m = String(totalMinutes % 60).padStart(2, "0");
  return `${h}:${m}`;
});

function findReservation(
  reservations: Reservation[],
  roomId: number,
  date: string,
  slot: string,
): Reservation | null {
  return (
    reservations.find(
      (r) => r.room_id === roomId && r.date === date && r.start_time <= slot && r.end_time > slot,
    ) ?? null
  );
}

export function RoomTimeGrid({ rooms, reservations, date, currentUserId, onCellClick }: Props) {
  return (
    <table>
      <thead>
        <tr>
          <th>時間帯</th>
          {rooms.map((room) => (
            <th key={room.id}>{room.name}</th>
          ))}
        </tr>
      </thead>
      <tbody>
        {TIME_SLOTS.map((slot) => (
          <tr key={slot}>
            <td>{slot}</td>
            {rooms.map((room) => {
              const reservation = findReservation(reservations, room.id, date, slot);
              const isMine = reservation != null && reservation.user_id === currentUserId;
              const clickable = reservation == null || isMine;
              return (
                <td key={room.id}>
                  <button
                    type="button"
                    disabled={!clickable}
                    onClick={() => clickable && onCellClick(room, reservation)}
                    data-testid={`cell-${room.id}-${slot}`}
                  >
                    {reservation ? `${reservation.user_name} / ${reservation.title}` : "空き"}
                  </button>
                </td>
              );
            })}
          </tr>
        ))}
      </tbody>
    </table>
  );
}
