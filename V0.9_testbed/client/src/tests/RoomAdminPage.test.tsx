import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { RoomAdminPage } from "../pages/RoomAdminPage";
import * as apiClient from "../api/client";

const ROOMS = [
  { id: 1, name: "会議室A", capacity: 10, equipment: [], description: "窓あり", is_active: true },
];

function renderPage() {
  render(
    <MemoryRouter>
      <RoomAdminPage />
    </MemoryRouter>,
  );
}

describe("RoomAdminPage", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    vi.spyOn(window, "confirm").mockReturnValue(true);
  });

  it("管理者ロールでアクセスすると会議室一覧・フォームが表示される", async () => {
    vi.spyOn(apiClient, "apiFetch").mockImplementation(async (path: string) => {
      if (path === "/api/me") return { id: 1, employee_id: "admin001", name: "管理者太郎", role: "admin" };
      if (path.startsWith("/api/rooms")) return ROOMS;
      throw new Error(`unexpected path: ${path}`);
    });

    renderPage();

    expect(await screen.findByText("会議室A")).toBeInTheDocument();
    expect(screen.getByLabelText("会議室名")).toBeInTheDocument();
  });

  it("一般ユーザーロールでアクセスすると権限不足の案内が表示され、フォームがDOMに存在しない", async () => {
    vi.spyOn(apiClient, "apiFetch").mockImplementation(async (path: string) => {
      if (path === "/api/me") return { id: 2, employee_id: "user001", name: "一般花子", role: "general" };
      throw new Error(`unexpected path: ${path}`);
    });

    renderPage();

    expect(await screen.findByText("この画面を表示する権限がありません。")).toBeInTheDocument();
    expect(screen.queryByLabelText("会議室名")).not.toBeInTheDocument();
  });

  it("削除ボタン押下→確認→DELETE /api/rooms/{id}が呼ばれる", async () => {
    const apiFetchSpy = vi.spyOn(apiClient, "apiFetch").mockImplementation(async (path: string, options) => {
      if (path === "/api/me") return { id: 1, employee_id: "admin001", name: "管理者太郎", role: "admin" };
      if (path.startsWith("/api/rooms") && (!options || options.method === undefined)) return ROOMS;
      if (path === "/api/rooms/1" && options?.method === "DELETE") return undefined;
      throw new Error(`unexpected call: ${path} ${options?.method}`);
    });

    renderPage();
    const user = userEvent.setup();

    await screen.findByText("会議室A");
    await user.click(screen.getByRole("button", { name: "削除" }));

    await waitFor(() => {
      expect(apiFetchSpy).toHaveBeenCalledWith("/api/rooms/1", expect.objectContaining({ method: "DELETE" }));
    });
  });
});
