import { apiFetch } from "./client";

export interface Room {
  id: number;
  name: string;
  capacity: number;
  equipment: string[];
  description: string | null;
  is_active: boolean;
}

export interface RoomInput {
  name: string;
  capacity: number;
  equipment?: string[];
  description?: string | null;
  is_active?: boolean;
}

export function fetchRooms(includeInactive = false): Promise<Room[]> {
  const query = includeInactive ? "?include_inactive=true" : "";
  return apiFetch<Room[]>(`/api/rooms${query}`);
}

export function createRoom(input: RoomInput): Promise<Room> {
  return apiFetch<Room>("/api/rooms", { method: "POST", body: JSON.stringify(input) });
}

export function updateRoom(id: number, input: RoomInput): Promise<Room> {
  return apiFetch<Room>(`/api/rooms/${id}`, { method: "PUT", body: JSON.stringify(input) });
}

export function deleteRoom(id: number): Promise<void> {
  return apiFetch<void>(`/api/rooms/${id}`, { method: "DELETE" });
}
