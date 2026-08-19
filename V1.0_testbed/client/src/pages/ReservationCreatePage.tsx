// S03 予約作成画面。docs/P002-frontend-spec.md §3 S03, §7.2。
import { useEffect, useState, type FormEvent } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { ApiError } from "../api/client";
import { createReservation } from "../api/reservations";
import { fetchRooms, type Room } from "../api/rooms";

export function ReservationCreatePage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const [rooms, setRooms] = useState<Room[]>([]);
  const [roomId, setRoomId] = useState<number | "">(() => {
    const fromQuery = searchParams.get("room_id");
    return fromQuery ? Number(fromQuery) : "";
  });
  const [date, setDate] = useState(searchParams.get("date") ?? "");
  const [startTime, setStartTime] = useState("");
  const [endTime, setEndTime] = useState("");
  const [allDay, setAllDay] = useState(false);
  const [title, setTitle] = useState("");
  const [expectedAttendees, setExpectedAttendees] = useState("");
  const [notes, setNotes] = useState("");
  const [internalMemo, setInternalMemo] = useState(""); // ※CR-001により追加
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    fetchRooms().then(setRooms);
  }, []);

  function handleAllDayChange(checked: boolean) {
    setAllDay(checked);
    if (checked) {
      setStartTime("09:00");
      setEndTime("18:00");
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setErrorMessage(null);

    if (endTime <= startTime) {
      setErrorMessage("終了時刻は開始時刻より後の時刻を指定してください");
      return;
    }
    if (!title) {
      setErrorMessage("件名を入力してください(100文字以内)");
      return;
    }

    setSubmitting(true);
    try {
      await createReservation({
        room_id: Number(roomId),
        date,
        start_time: startTime,
        end_time: endTime,
        title,
        // 参加者選択は現状未実装(docs/P007-impl-direction.md 未解決事項を参照)。
        participant_ids: [],
        expected_attendees: expectedAttendees ? Number(expectedAttendees) : null,
        notes: notes || null,
        internal_memo: internalMemo || null, // ※CR-001により追加
      });
      navigate("/calendar");
    } catch (error) {
      if (error instanceof ApiError && error.errorCode === "RESERVATION_CONFLICT") {
        setErrorMessage("選択した会議室・時間帯は既に予約されています");
      } else if (error instanceof ApiError && error.errorCode === "CAPACITY_EXCEEDED") {
        setErrorMessage("参加予定人数が会議室の収容人数を超えています");
      } else if (error instanceof ApiError) {
        setErrorMessage(error.message);
      } else {
        setErrorMessage("登録に失敗しました。時間をおいて再度お試しください。");
      }
    } finally {
      setSubmitting(false);
    }
  }

  function handleCancel() {
    navigate("/calendar");
  }

  return (
    <main>
      <h1>予約作成</h1>
      <form onSubmit={handleSubmit}>
        <div>
          <label htmlFor="room">会議室</label>
          <select id="room" value={roomId} onChange={(e) => setRoomId(Number(e.target.value))} required>
            <option value="">選択してください</option>
            {rooms.map((room) => (
              <option key={room.id} value={room.id}>
                {room.name}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label htmlFor="date">日付</label>
          <input id="date" type="date" value={date} onChange={(e) => setDate(e.target.value)} required />
        </div>
        <div>
          <label htmlFor="allDay">終日</label>
          <input
            id="allDay"
            type="checkbox"
            checked={allDay}
            onChange={(e) => handleAllDayChange(e.target.checked)}
          />
        </div>
        <div>
          <label htmlFor="startTime">開始時刻</label>
          <input
            id="startTime"
            type="time"
            value={startTime}
            onChange={(e) => setStartTime(e.target.value)}
            required
          />
        </div>
        <div>
          <label htmlFor="endTime">終了時刻</label>
          <input id="endTime" type="time" value={endTime} onChange={(e) => setEndTime(e.target.value)} required />
        </div>
        <div>
          <label htmlFor="title">件名</label>
          <input
            id="title"
            type="text"
            maxLength={100}
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            required
          />
        </div>
        <div>
          <p>
            参加者(社員)の選択は現在ご利用いただけません。社員一覧を取得するAPIが管理者専用のため
            (詳細は開発チームの未解決事項一覧を参照)。
          </p>
        </div>
        <div>
          <label htmlFor="expectedAttendees">参加予定人数</label>
          <input
            id="expectedAttendees"
            type="number"
            min={1}
            value={expectedAttendees}
            onChange={(e) => setExpectedAttendees(e.target.value)}
          />
        </div>
        <div>
          <label htmlFor="notes">備考</label>
          <textarea id="notes" maxLength={500} value={notes} onChange={(e) => setNotes(e.target.value)} />
        </div>
        <div>
          {/* ※CR-001により追加。所有者・管理者のみ閲覧可能(docs/P002-frontend-spec.md §6参照)。 */}
          <label htmlFor="internalMemo">備考(社内向けメモ)</label>
          <textarea
            id="internalMemo"
            maxLength={300}
            value={internalMemo}
            onChange={(e) => setInternalMemo(e.target.value)}
          />
        </div>
        {errorMessage && <p role="alert">{errorMessage}</p>}
        <button type="submit" disabled={submitting}>
          登録
        </button>
        <button type="button" onClick={handleCancel}>
          キャンセル
        </button>
      </form>
    </main>
  );
}
