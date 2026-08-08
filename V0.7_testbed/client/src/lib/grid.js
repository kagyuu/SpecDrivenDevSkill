// 予約配列から「(日付, 会議室, スロット) → 予約 or null」の占有マップを作る純粋関数(P002 3.2)。
// DOMにも api.js にも依存しない。U004-T1。

import { toMinutes } from './datetime.js';

export function slotKey(date, roomId, slot) {
  return `${date}|${roomId}|${slot}`;
}

// 予約が占有するスロットの一覧。**終了時刻のスロットは占有しない**(半開区間 [start, end))。
// 例: 09:00-10:00 の予約は 09:00 と 09:30 のみを占有する(P002 3.2 / ADR-007)。
export function occupiedSlots(reservation, slots) {
  const start = toMinutes(reservation.start_time);
  const end = toMinutes(reservation.end_time);
  return slots.filter((slot) => {
    const at = toMinutes(slot);
    return at >= start && at < end;
  });
}

// 占有マップを構築する。同じセルに複数の予約が来た場合は先に現れたものを優先する
// (サーバー側の重複チェックにより通常は発生しない)。
export function buildOccupancy(reservations, slots) {
  const map = new Map();
  for (const reservation of reservations || []) {
    for (const slot of occupiedSlots(reservation, slots)) {
      const key = slotKey(reservation.reserved_date, reservation.room_id, slot);
      if (!map.has(key)) map.set(key, reservation);
    }
  }
  return map;
}

export function reservationAt(occupancy, date, roomId, slot) {
  return occupancy.get(slotKey(date, roomId, slot)) || null;
}

// 会議室フィルタ(クライアント側で絞り込む。未選択なら全件。P002 3.2)
export function filterRooms(rooms, selectedRoomIds) {
  const list = rooms || [];
  if (!selectedRoomIds || selectedRoomIds.length === 0) return list;
  const selected = new Set(selectedRoomIds.map(String));
  return list.filter((room) => selected.has(String(room.room_id)));
}

// セルの表示文言。予約済みは「予約者の氏名 / 件名」。参加予定人数は表示しない(P002 3.2)。
export function cellLabel(reservation) {
  if (!reservation) return '+';
  return `${reservation.user_name} / ${reservation.title}`;
}
