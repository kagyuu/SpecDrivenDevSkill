import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { ReservationCreatePage } from "../pages/ReservationCreatePage";
import * as apiClient from "../api/client";

const ROOMS = [{ id: 10, name: "会議室A", capacity: 10, equipment: [], description: null, is_active: true }];

function renderPage() {
  render(
    <MemoryRouter initialEntries={["/reservations/new?room_id=10&date=2026-08-12"]}>
      <Routes>
        <Route path="/reservations/new" element={<ReservationCreatePage />} />
        <Route path="/calendar" element={<div>calendar-placeholder</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("ReservationCreatePage", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("終日チェックボックスをオンにすると開始09:00・終了18:00が入力される", async () => {
    vi.spyOn(apiClient, "apiFetch").mockImplementation(async (path: string) => {
      if (path === "/api/rooms") return ROOMS;
      throw new Error(`unexpected path: ${path}`);
    });

    renderPage();
    const user = userEvent.setup();
    await user.click(await screen.findByLabelText("終日"));

    expect(screen.getByLabelText("開始時刻")).toHaveValue("09:00");
    expect(screen.getByLabelText("終了時刻")).toHaveValue("18:00");
  });

  it("終了時刻を開始時刻以前にして送信すると、APIを呼ばずにエラーを表示する", async () => {
    const apiFetchSpy = vi.spyOn(apiClient, "apiFetch").mockImplementation(async (path: string) => {
      if (path === "/api/rooms") return ROOMS;
      throw new Error(`unexpected path: ${path}`);
    });

    renderPage();
    const user = userEvent.setup();

    await user.selectOptions(await screen.findByLabelText("会議室"), "10");
    await user.type(screen.getByLabelText("開始時刻"), "10:00");
    await user.type(screen.getByLabelText("終了時刻"), "09:00");
    await user.type(screen.getByLabelText("件名"), "テスト会議");
    await user.click(screen.getByRole("button", { name: "登録" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "終了時刻は開始時刻より後の時刻を指定してください",
    );
    expect(apiFetchSpy).not.toHaveBeenCalledWith("/api/reservations", expect.anything());
  });

  it("APIが409を返すと重複メッセージを表示する", async () => {
    vi.spyOn(apiClient, "apiFetch").mockImplementation(async (path: string) => {
      if (path === "/api/rooms") return ROOMS;
      if (path === "/api/reservations") {
        throw new apiClient.ApiError(409, {
          error_code: "RESERVATION_CONFLICT",
          message: "選択した会議室・時間帯は既に予約されています",
        });
      }
      throw new Error(`unexpected path: ${path}`);
    });

    renderPage();
    const user = userEvent.setup();

    await user.selectOptions(await screen.findByLabelText("会議室"), "10");
    await user.type(screen.getByLabelText("開始時刻"), "10:00");
    await user.type(screen.getByLabelText("終了時刻"), "11:00");
    await user.type(screen.getByLabelText("件名"), "テスト会議");
    await user.click(screen.getByRole("button", { name: "登録" }));

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent("選択した会議室・時間帯は既に予約されています");
    });
  });

  // ※CR-001により追加。

  it("備考(社内向けメモ)欄が最大300文字で表示され、入力内容が送信payloadに含まれる", async () => {
    let capturedBody: string | undefined;
    vi.spyOn(apiClient, "apiFetch").mockImplementation(async (path: string, init?: RequestInit) => {
      if (path === "/api/rooms") return ROOMS;
      if (path === "/api/reservations") {
        capturedBody = init?.body as string;
        return { id: 1 };
      }
      throw new Error(`unexpected path: ${path}`);
    });

    renderPage();
    const user = userEvent.setup();

    const memoField = await screen.findByLabelText("備考(社内向けメモ)");
    expect(memoField).toHaveAttribute("maxlength", "300");

    await user.selectOptions(screen.getByLabelText("会議室"), "10");
    await user.type(screen.getByLabelText("開始時刻"), "10:00");
    await user.type(screen.getByLabelText("終了時刻"), "11:00");
    await user.type(screen.getByLabelText("件名"), "テスト会議");
    await user.type(memoField, "社外秘のメモ");
    await user.click(screen.getByRole("button", { name: "登録" }));

    await waitFor(() => {
      expect(capturedBody).toBeDefined();
    });
    expect(JSON.parse(capturedBody!).internal_memo).toBe("社外秘のメモ");
  });
});
