// S05 マイ予約一覧画面。docs/P002-frontend-spec.md §3 S05。
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { fetchMyReservations, type Reservation } from "../api/reservations";

type Period = "upcoming" | "past";

export function MyReservationsPage() {
  const [period, setPeriod] = useState<Period>("upcoming");
  const [reservations, setReservations] = useState<Reservation[]>([]);
  const navigate = useNavigate();

  useEffect(() => {
    fetchMyReservations(period).then(setReservations);
  }, [period]);

  return (
    <main>
      <h1>マイ予約一覧</h1>
      <label htmlFor="period-filter">期間</label>
      <select id="period-filter" value={period} onChange={(e) => setPeriod(e.target.value as Period)}>
        <option value="upcoming">今後の予約</option>
        <option value="past">過去の予約</option>
      </select>
      <table>
        <thead>
          <tr>
            <th>日付</th>
            <th>会議室</th>
            <th>時間帯</th>
            <th>件名</th>
          </tr>
        </thead>
        <tbody>
          {reservations.map((reservation) => (
            <tr key={reservation.id}>
              <td>
                <button type="button" onClick={() => navigate(`/reservations/${reservation.id}`)}>
                  {reservation.date}
                </button>
              </td>
              <td>{reservation.room_name}</td>
              <td>
                {reservation.start_time}-{reservation.end_time}
              </td>
              <td>{reservation.title}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </main>
  );
}
