// S02 予約カレンダー画面(トップ)。docs/P002-frontend-spec.md §3 S02, §4, §10。
import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { apiFetch } from "../api/client";
import { fetchReservations, type Reservation } from "../api/reservations";
import { fetchRooms, type Room } from "../api/rooms";
import { RoomTimeGrid } from "../components/RoomTimeGrid";

interface Me {
  id: number;
  employee_id: string;
  name: string;
  role: string;
}

function startOfWeek(date: Date): Date {
  const d = new Date(date);
  const day = (d.getDay() + 6) % 7; // 月曜=0
  d.setDate(d.getDate() - day);
  d.setHours(0, 0, 0, 0);
  return d;
}

function toDateString(date: Date): string {
  // ※P202 F002にもとづき修正: toISOString()はUTC基準で変換するため、
  // ローカルタイムゾーンによっては「ローカルの今日」と1日ずれることがあった。
  // ローカルタイムゾーン基準の年月日から直接組み立てる。
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function addDays(date: Date, days: number): Date {
  const d = new Date(date);
  d.setDate(d.getDate() + days);
  return d;
}

export function CalendarPage() {
  const [me, setMe] = useState<Me | null>(null);
  const [rooms, setRooms] = useState<Room[]>([]);
  const [reservations, setReservations] = useState<Reservation[]>([]);
  const [weekStart, setWeekStart] = useState(() => startOfWeek(new Date()));
  const [selectedDate, setSelectedDate] = useState(() => toDateString(new Date()));
  const [roomFilter, setRoomFilter] = useState<number | "">("");
  const navigate = useNavigate();

  const weekDays = useMemo(
    () => Array.from({ length: 7 }, (_, i) => toDateString(addDays(weekStart, i))),
    [weekStart],
  );

  useEffect(() => {
    apiFetch<Me>("/api/me")
      .then(setMe)
      .catch(() => navigate("/"));
  }, [navigate]);

  useEffect(() => {
    fetchRooms().then(setRooms);
  }, []);

  useEffect(() => {
    const dateFrom = weekDays[0];
    const dateTo = weekDays[6];
    fetchReservations({
      dateFrom,
      dateTo,
      roomId: roomFilter === "" ? undefined : roomFilter,
    }).then(setReservations);
  }, [weekDays, roomFilter]);

  const visibleRooms = roomFilter === "" ? rooms : rooms.filter((r) => r.id === roomFilter);

  async function handleLogout() {
    await apiFetch("/api/auth/logout", { method: "POST" });
    navigate("/");
  }

  if (!me) {
    return <main>読み込み中...</main>;
  }

  return (
    <main>
      <h1>予約カレンダー</h1>
      <nav>
        <span>{me.name} さん</span>
        <button type="button" onClick={() => setWeekStart((w) => addDays(w, -7))}>
          前週
        </button>
        <button type="button" onClick={() => setWeekStart((w) => addDays(w, 7))}>
          翌週
        </button>
        {me.role === "admin" && <a href="/rooms">会議室管理</a>}
        {me.role === "admin" && <a href="/users">ユーザー管理</a>}
        <a href="/my-reservations">マイ予約</a>
        <button type="button" onClick={handleLogout}>
          ログアウト
        </button>
      </nav>
      <label htmlFor="room-filter">会議室フィルタ</label>
      <select
        id="room-filter"
        value={roomFilter}
        onChange={(e) => setRoomFilter(e.target.value === "" ? "" : Number(e.target.value))}
      >
        <option value="">すべて</option>
        {rooms.map((room) => (
          <option key={room.id} value={room.id}>
            {room.name}
          </option>
        ))}
      </select>
      <div>
        {weekDays.map((day) => (
          <button
            key={day}
            type="button"
            aria-pressed={day === selectedDate}
            onClick={() => setSelectedDate(day)}
          >
            {day}
          </button>
        ))}
      </div>
      <RoomTimeGrid
        rooms={visibleRooms}
        reservations={reservations}
        date={selectedDate}
        currentUserId={me.id}
        onCellClick={(room, reservation) => {
          if (reservation) {
            navigate(`/reservations/${reservation.id}`);
          } else {
            navigate(`/reservations/new?room_id=${room.id}&date=${selectedDate}`);
          }
        }}
      />
    </main>
  );
}
