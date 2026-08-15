import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { ReservationDetailPage } from "../pages/ReservationDetailPage";
import * as apiClient from "../api/client";
import * as reservationsApi from "../api/reservations";

const RESERVATION = {
  id: 5,
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
  internal_memo: "非公開メモ", // ※CR-001により追加
};

function renderPage() {
  render(
    <MemoryRouter initialEntries={["/reservations/5"]}>
      <Routes>
        <Route path="/reservations/:id" element={<ReservationDetailPage />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("ReservationDetailPage", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    vi.spyOn(reservationsApi, "fetchReservation").mockResolvedValue(RESERVATION);
  });

  it("予約者本人としてアクセスすると編集フォーム・取消ボタンが表示される", async () => {
    vi.spyOn(apiClient, "apiFetch").mockResolvedValue({
      id: 1,
      employee_id: "user001",
      name: "一般花子",
      role: "general",
    });

    renderPage();

    expect(await screen.findByLabelText("件名")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "更新" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "取消" })).toBeInTheDocument();
  });

  it("他人の予約に一般ユーザーとしてアクセスすると編集フォーム・取消ボタンがDOMに存在しない", async () => {
    vi.spyOn(apiClient, "apiFetch").mockResolvedValue({
      id: 999,
      employee_id: "user002",
      name: "他人次郎",
      role: "general",
    });

    renderPage();

    expect(await screen.findByText(/表示のみ/)).toBeInTheDocument();
    expect(screen.queryByLabelText("件名")).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "取消" })).not.toBeInTheDocument();
  });

  it("管理者としてアクセスすると他人の予約でも編集フォーム・取消ボタンが表示される", async () => {
    vi.spyOn(apiClient, "apiFetch").mockResolvedValue({
      id: 999,
      employee_id: "admin001",
      name: "管理者太郎",
      role: "admin",
    });

    renderPage();

    expect(await screen.findByLabelText("件名")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "取消" })).toBeInTheDocument();
  });

  // ※CR-001により追加。

  it("予約者本人としてアクセスすると備考(社内向けメモ)欄に値が表示される", async () => {
    vi.spyOn(apiClient, "apiFetch").mockResolvedValue({
      id: 1,
      employee_id: "user001",
      name: "一般花子",
      role: "general",
    });

    renderPage();

    expect(await screen.findByLabelText("備考(社内向けメモ)")).toHaveValue("非公開メモ");
  });

  it("他人の予約に一般ユーザーとしてアクセスすると備考(社内向けメモ)欄自体がDOMに存在しない", async () => {
    vi.spyOn(apiClient, "apiFetch").mockResolvedValue({
      id: 999,
      employee_id: "user002",
      name: "他人次郎",
      role: "general",
    });

    renderPage();

    await screen.findByText(/表示のみ/);
    expect(screen.queryByLabelText("備考(社内向けメモ)")).not.toBeInTheDocument();
  });
});
