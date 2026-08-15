// S04 予約詳細・編集画面。docs/P002-frontend-spec.md §3 S04, §7.3, §6。
import { useEffect, useState, type FormEvent } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { apiFetch, ApiError } from "../api/client";
import {
  deleteReservation,
  fetchReservation,
  updateReservation,
  type Reservation,
} from "../api/reservations";

interface Me {
  id: number;
  employee_id: string;
  name: string;
  role: string;
}

export function ReservationDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [me, setMe] = useState<Me | null>(null);
  const [reservation, setReservation] = useState<Reservation | null>(null);
  const [title, setTitle] = useState("");
  const [startTime, setStartTime] = useState("");
  const [endTime, setEndTime] = useState("");
  const [internalMemo, setInternalMemo] = useState(""); // ※CR-001により追加
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    apiFetch<Me>("/api/me").then(setMe);
  }, []);

  useEffect(() => {
    if (!id) return;
    fetchReservation(Number(id)).then((r) => {
      setReservation(r);
      setTitle(r.title);
      setStartTime(r.start_time);
      setEndTime(r.end_time);
      setInternalMemo(r.internal_memo ?? ""); // ※CR-001により追加
    });
  }, [id]);

  if (!me || !reservation) {
    return <main>読み込み中...</main>;
  }

  const canEdit = me.role === "admin" || me.id === reservation.user_id;

  async function handleUpdate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setErrorMessage(null);
    if (endTime <= startTime) {
      setErrorMessage("終了時刻は開始時刻より後の時刻を指定してください");
      return;
    }
    try {
      await updateReservation(reservation!.id, {
        room_id: reservation!.room_id,
        date: reservation!.date,
        start_time: startTime,
        end_time: endTime,
        title,
        participant_ids: reservation!.participant_ids,
        expected_attendees: reservation!.expected_attendees,
        notes: reservation!.notes,
        internal_memo: internalMemo || null, // ※CR-001により追加
      });
      navigate("/calendar");
    } catch (error) {
      if (error instanceof ApiError && error.errorCode === "RESERVATION_CONFLICT") {
        setErrorMessage("選択した会議室・時間帯は既に予約されています");
      } else if (error instanceof ApiError) {
        setErrorMessage(error.message);
      }
    }
  }

  async function handleCancelReservation() {
    if (!window.confirm("この予約を取り消しますか?")) {
      return;
    }
    await deleteReservation(reservation!.id);
    navigate("/calendar");
  }

  return (
    <main>
      <h1>予約詳細</h1>
      <dl>
        <dt>会議室</dt>
        <dd>{reservation.room_name}</dd>
        <dt>日付</dt>
        <dd>{reservation.date}</dd>
        <dt>予約者</dt>
        <dd>{reservation.user_name}</dd>
      </dl>

      {!canEdit && <p>表示のみ(この予約を編集・取消する権限がありません)</p>}

      {canEdit && (
        <form onSubmit={handleUpdate}>
          <div>
            <label htmlFor="title">件名</label>
            <input id="title" value={title} onChange={(e) => setTitle(e.target.value)} />
          </div>
          <div>
            <label htmlFor="startTime">開始時刻</label>
            <input id="startTime" type="time" value={startTime} onChange={(e) => setStartTime(e.target.value)} />
          </div>
          <div>
            <label htmlFor="endTime">終了時刻</label>
            <input id="endTime" type="time" value={endTime} onChange={(e) => setEndTime(e.target.value)} />
          </div>
          <div>
            {/* ※CR-001により追加。canEdit(所有者・管理者)の条件がAPI側のマスキング閲覧条件と一致するため、
                このフォーム内に配置している(docs/P002-frontend-spec.md §6参照)。 */}
            <label htmlFor="internalMemo">備考(社内向けメモ)</label>
            <textarea
              id="internalMemo"
              maxLength={300}
              value={internalMemo}
              onChange={(e) => setInternalMemo(e.target.value)}
            />
          </div>
          {errorMessage && <p role="alert">{errorMessage}</p>}
          <button type="submit">更新</button>
          <button type="button" onClick={handleCancelReservation}>
            取消
          </button>
        </form>
      )}
    </main>
  );
}
