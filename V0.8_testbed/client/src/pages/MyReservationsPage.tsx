// U004-T4 (docs/P007-impl-direction/U004-reservation-detail-and-mylist.md):
// S05マイ予約一覧画面 (docs/P002-frontend-spec.md 3.5節)。
// ★U005-T4改訂: 共通Headerコンポーネントを追加した(この画面はU004-T4時点では
// ヘッダーを持っていなかった)。
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import {
  reservationApi,
  type MyReservationListItem,
  type MyReservationsPeriod,
} from '../api/reservationApi'
import { Header } from '../components/Header'

const PERIOD_LABELS: Record<MyReservationsPeriod, string> = {
  upcoming: '今後の予約',
  past: '過去の予約',
  all: 'すべて',
}

export function MyReservationsPage() {
  const navigate = useNavigate()
  const [period, setPeriod] = useState<MyReservationsPeriod>('upcoming')
  const [items, setItems] = useState<MyReservationListItem[]>([])
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    reservationApi
      .listMyReservations(period)
      .then((result) => {
        setItems(result)
        setError(null)
      })
      .catch(() => setError('マイ予約一覧の取得に失敗しました'))
  }, [period])

  return (
    <div>
      <Header currentScreen="S05" />

      <h1>マイ予約</h1>
      {error && <p role="alert">{error}</p>}

      <fieldset>
        <legend>期間フィルタ</legend>
        {(Object.keys(PERIOD_LABELS) as MyReservationsPeriod[]).map((value) => (
          <label key={value}>
            <input
              type="radio"
              name="period"
              value={value}
              checked={period === value}
              onChange={() => setPeriod(value)}
            />
            {PERIOD_LABELS[value]}
          </label>
        ))}
      </fieldset>

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
          {items.map((item) => (
            <tr key={item.reservation_id}>
              <td>
                <button type="button" onClick={() => navigate(`/reservations/${item.reservation_id}`)}>
                  {item.date}
                </button>
              </td>
              <td>{item.room_name}</td>
              <td>
                {item.start_time}〜{item.end_time}
              </td>
              <td>{item.title}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default MyReservationsPage
