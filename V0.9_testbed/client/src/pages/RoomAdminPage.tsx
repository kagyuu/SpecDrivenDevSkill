// S06 会議室管理画面(管理者用)。docs/P002-frontend-spec.md §3 S06, §6。
import { useEffect, useState, type FormEvent } from "react";
import { apiFetch } from "../api/client";
import { createRoom, deleteRoom, fetchRooms, type Room } from "../api/rooms";

interface Me {
  id: number;
  employee_id: string;
  name: string;
  role: string;
}

export function RoomAdminPage() {
  const [me, setMe] = useState<Me | null>(null);
  const [rooms, setRooms] = useState<Room[]>([]);
  const [name, setName] = useState("");
  const [capacity, setCapacity] = useState("");
  const [description, setDescription] = useState("");

  useEffect(() => {
    apiFetch<Me>("/api/me").then(setMe);
  }, []);

  function reload() {
    fetchRooms(true).then(setRooms);
  }

  useEffect(() => {
    if (me?.role === "admin") {
      reload();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [me]);

  if (!me) {
    return <main>読み込み中...</main>;
  }

  if (me.role !== "admin") {
    return <main>この画面を表示する権限がありません。</main>;
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await createRoom({ name, capacity: Number(capacity), description: description || null });
    setName("");
    setCapacity("");
    setDescription("");
    reload();
  }

  async function handleDelete(room: Room) {
    if (!window.confirm(`会議室「${room.name}」を削除しますか?`)) {
      return;
    }
    await deleteRoom(room.id);
    reload();
  }

  return (
    <main>
      <h1>会議室管理</h1>
      <table>
        <thead>
          <tr>
            <th>会議室名</th>
            <th>収容人数</th>
            <th>説明文</th>
            <th>状態</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          {rooms.map((room) => (
            <tr key={room.id}>
              <td>{room.name}</td>
              <td>{room.capacity}</td>
              <td>{room.description}</td>
              <td>{room.is_active ? "有効" : "無効"}</td>
              <td>
                {room.is_active && (
                  <button type="button" onClick={() => handleDelete(room)}>
                    削除
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <h2>新規登録</h2>
      <form onSubmit={handleSubmit}>
        <div>
          <label htmlFor="room-name">会議室名</label>
          <input id="room-name" value={name} onChange={(e) => setName(e.target.value)} required maxLength={50} />
        </div>
        <div>
          <label htmlFor="room-capacity">収容人数</label>
          <input
            id="room-capacity"
            type="number"
            min={1}
            value={capacity}
            onChange={(e) => setCapacity(e.target.value)}
            required
          />
        </div>
        <div>
          <label htmlFor="room-description">説明文</label>
          <input
            id="room-description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            maxLength={200}
          />
        </div>
        <button type="submit">登録</button>
      </form>
    </main>
  );
}
