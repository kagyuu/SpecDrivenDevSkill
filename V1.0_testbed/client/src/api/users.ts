import { apiFetch } from "./client";

export interface AppUser {
  id: number;
  employee_id: string;
  name: string;
  role: "general" | "admin";
  is_active: boolean;
}

export interface UserCreateInput {
  employee_id: string;
  name: string;
  role: "general" | "admin";
  is_active?: boolean;
  initial_password: string;
}

export function fetchUsers(): Promise<AppUser[]> {
  return apiFetch<AppUser[]>("/api/users");
}

export function createUser(input: UserCreateInput): Promise<AppUser> {
  return apiFetch<AppUser>("/api/users", { method: "POST", body: JSON.stringify(input) });
}

export function deactivateUser(id: number): Promise<void> {
  return apiFetch<void>(`/api/users/${id}`, { method: "DELETE" });
}
