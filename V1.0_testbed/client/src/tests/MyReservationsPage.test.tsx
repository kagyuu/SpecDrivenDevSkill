import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { MyReservationsPage } from "../pages/MyReservationsPage";
import * as apiClient from "../api/client";

function renderPage() {
  render(
    <MemoryRouter initialEntries={["/my-reservations"]}>
      <Routes>
        <Route path="/my-reservations" element={<MyReservationsPage />} />
        <Route path="/reservations/:id" element={<div>detail-placeholder</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("MyReservationsPage", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("期間フィルタの切り替えでGET /api/reservations/mineを異なるクエリで呼び直す", async () => {
    const apiFetchSpy = vi.spyOn(apiClient, "apiFetch").mockResolvedValue([]);

    renderPage();

    await waitFor(() => {
      expect(apiFetchSpy).toHaveBeenCalledWith("/api/reservations/mine?period=upcoming");
    });

    const user = userEvent.setup();
    await user.selectOptions(screen.getByLabelText("期間"), "past");

    await waitFor(() => {
      expect(apiFetchSpy).toHaveBeenCalledWith("/api/reservations/mine?period=past");
    });
  });

  it("取得した予約一覧が表示される", async () => {
    vi.spyOn(apiClient, "apiFetch").mockResolvedValue([
      {
        id: 1,
        room_id: 10,
        room_name: "会議室A",
        user_id: 1,
        user_name: "一般花子",
        date: "2026-08-12",
        start_time: "10:00",
        end_time: "11:00",
        title: "定例MTG",
        participant_ids: [],
        expected_attendees: null,
        notes: null,
      },
    ]);

    renderPage();

    expect(await screen.findByText("定例MTG")).toBeInTheDocument();
    expect(screen.getByText("会議室A")).toBeInTheDocument();
  });
});
