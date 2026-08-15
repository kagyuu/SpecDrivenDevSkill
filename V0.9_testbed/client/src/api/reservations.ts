import { apiFetch } from "./client";

export interface Reservation {
  id: number;
  room_id: number;
  room_name: string;
  user_id: number;
  user_name: string;
  date: string;
  start_time: string;
  end_time: string;
  title: string;
  participant_ids: number[];
  expected_attendees: number | null;
  notes: string | null;
  internal_memo: string | null; // ※CR-001により追加。所有者・管理者以外にはAPIでnullが返る
}

export interface ReservationInput {
  room_id: number;
  date: string;
  start_time: string;
  end_time: string;
  title: string;
  participant_ids?: number[];
  expected_attendees?: number | null;
  notes?: string | null;
  internal_memo?: string | null; // ※CR-001により追加
}

export function fetchReservations(params: {
  dateFrom: string;
  dateTo: string;
  roomId?: number;
}): Promise<Reservation[]> {
  const search = new URLSearchParams({ date_from: params.dateFrom, date_to: params.dateTo });
  if (params.roomId != null) {
    search.set("room_id", String(params.roomId));
  }
  return apiFetch<Reservation[]>(`/api/reservations?${search.toString()}`);
}

export function fetchMyReservations(period: "upcoming" | "past"): Promise<Reservation[]> {
  return apiFetch<Reservation[]>(`/api/reservations/mine?period=${period}`);
}

export function fetchReservation(id: number): Promise<Reservation> {
  return apiFetch<Reservation>(`/api/reservations/${id}`);
}

export function createReservation(input: ReservationInput): Promise<Reservation> {
  return apiFetch<Reservation>("/api/reservations", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function updateReservation(id: number, input: ReservationInput): Promise<Reservation> {
  return apiFetch<Reservation>(`/api/reservations/${id}`, {
    method: "PUT",
    body: JSON.stringify(input),
  });
}

export function deleteReservation(id: number): Promise<void> {
  return apiFetch<void>(`/api/reservations/${id}`, { method: "DELETE" });
}
