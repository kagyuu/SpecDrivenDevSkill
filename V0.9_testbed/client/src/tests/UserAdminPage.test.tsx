import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { UserAdminPage } from "../pages/UserAdminPage";
import * as apiClient from "../api/client";

const USERS = [
  { id: 1, employee_id: "admin001", name: "管理者太郎", role: "admin", is_active: true },
  { id: 2, employee_id: "user001", name: "一般花子", role: "general", is_active: true },
];

function renderPage() {
  render(
    <MemoryRouter>
      <UserAdminPage />
    </MemoryRouter>,
  );
}

describe("UserAdminPage", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("管理者としてアクセスするとユーザー一覧・フォームが表示される", async () => {
    vi.spyOn(apiClient, "apiFetch").mockImplementation(async (path: string) => {
      if (path === "/api/me") return { id: 1, employee_id: "admin001", name: "管理者太郎", role: "admin" };
      if (path === "/api/users") return USERS;
      throw new Error(`unexpected path: ${path}`);
    });

    renderPage();

    expect(await screen.findByText("一般花子")).toBeInTheDocument();
    expect(screen.getByLabelText("社員ID")).toBeInTheDocument();
  });

  it("自分自身の行の削除ボタンが無効化されている", async () => {
    vi.spyOn(apiClient, "apiFetch").mockImplementation(async (path: string) => {
      if (path === "/api/me") return { id: 1, employee_id: "admin001", name: "管理者太郎", role: "admin" };
      if (path === "/api/users") return USERS;
      throw new Error(`unexpected path: ${path}`);
    });

    renderPage();

    await screen.findByText("管理者太郎");
    const rows = screen.getAllByRole("row");
    const adminRow = rows.find((row) => row.textContent?.includes("管理者太郎"));
    const deleteButton = adminRow?.querySelector("button");
    expect(deleteButton).toBeDisabled();
  });

  it("一般ユーザーとしてアクセスすると権限不足の案内が表示され、フォームがDOMに存在しない", async () => {
    vi.spyOn(apiClient, "apiFetch").mockImplementation(async (path: string) => {
      if (path === "/api/me") return { id: 2, employee_id: "user001", name: "一般花子", role: "general" };
      throw new Error(`unexpected path: ${path}`);
    });

    renderPage();

    expect(await screen.findByText("この画面を表示する権限がありません。")).toBeInTheDocument();
    expect(screen.queryByLabelText("社員ID")).not.toBeInTheDocument();
  });
});
