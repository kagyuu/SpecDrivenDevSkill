import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { CalendarPage } from "../pages/CalendarPage";
import * as apiClient from "../api/client";

const ME = { id: 1, employee_id: "user001", name: "一般花子", role: "general" };
const ROOMS = [{ id: 10, name: "会議室A", capacity: 10, equipment: [], description: null, is_active: true }];

// ※P202 F002にもとづき修正: CalendarPage側がローカルタイムゾーン基準の日付文字列を使うようになったため、
// テストのフィクスチャもtoISOString()(UTC基準)ではなくローカル基準で「今日」を計算する。
function todayLocalDateString(): string {
  const d = new Date();
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function makeReservation(overrides: Partial<Record<string, unknown>> = {}) {
  return {
    id: 100,
    room_id: 10,
    room_name: "会議室A",
    user_id: 1,
    user_name: "一般花子",
    date: todayLocalDateString(),
    start_time: "10:00",
    end_time: "10:30",
    title: "自分の予約",
    participant_ids: [],
    expected_attendees: null,
    notes: null,
    ...overrides,
  };
}

function mockApiFetch(reservations: unknown[]) {
  return vi.spyOn(apiClient, "apiFetch").mockImplementation(async (path: string) => {
    if (path === "/api/me") return ME;
    if (path === "/api/rooms") return ROOMS;
    if (path.startsWith("/api/reservations?")) return reservations;
    if (path === "/api/auth/logout") return undefined;
    throw new Error(`unexpected path: ${path}`);
  });
}

function renderCalendarPage() {
  render(
    <MemoryRouter initialEntries={["/calendar"]}>
      <Routes>
        <Route path="/calendar" element={<CalendarPage />} />
        <Route path="/reservations/:id" element={<div>detail-placeholder</div>} />
        <Route path="/reservations/new" element={<div>create-placeholder</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("CalendarPage", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("APIから取得した予約が該当セルに表示される", async () => {
    mockApiFetch([makeReservation()]);
    renderCalendarPage();

    await waitFor(() => {
      expect(screen.getByText("一般花子 / 自分の予約")).toBeInTheDocument();
    });
  });

  it("自分の予約セルはクリック可能で詳細へ遷移する", async () => {
    mockApiFetch([makeReservation()]);
    renderCalendarPage();
    const user = userEvent.setup();

    const cell = await screen.findByText("一般花子 / 自分の予約");
    await user.click(cell);

    expect(await screen.findByText("detail-placeholder")).toBeInTheDocument();
  });

  it("他人の予約セルはクリックしても遷移しない(ボタンが無効化される)", async () => {
    mockApiFetch([makeReservation({ user_id: 999, user_name: "他人太郎" })]);
    renderCalendarPage();

    const cell = await screen.findByText("他人太郎 / 自分の予約");
    expect(cell.closest("button")).toBeDisabled();
  });

  // ※P202 F001にもとづき追加。
  it("ログインユーザー名が表示される", async () => {
    mockApiFetch([]);
    renderCalendarPage();

    expect(await screen.findByText("一般花子 さん")).toBeInTheDocument();
  });

  it("ログアウトボタン押下でログアウトAPIを呼びS01へ遷移する", async () => {
    const apiFetchSpy = mockApiFetch([]);
    renderCalendarPage();
    const user = userEvent.setup();

    await user.click(await screen.findByRole("button", { name: "ログアウト" }));

    await waitFor(() => {
      expect(apiFetchSpy).toHaveBeenCalledWith("/api/auth/logout", expect.objectContaining({ method: "POST" }));
    });
  });
});
