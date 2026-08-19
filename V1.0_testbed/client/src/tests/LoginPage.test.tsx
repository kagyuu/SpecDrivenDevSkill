import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { LoginPage } from "../pages/LoginPage";
import * as apiClient from "../api/client";

function renderLoginPage() {
  // 宣言的な MemoryRouter を使う(createMemoryRouter のデータルータAPIは、
  // jsdom環境でnavigate時にNode undiciのRequest/AbortSignalをクロスレルム構築しようとして
  // 無関係なUnhandled Rejectionを出すことがあるため、単体テストの範囲ではこちらを避ける)。
  render(
    <MemoryRouter initialEntries={["/"]}>
      <Routes>
        <Route path="/" element={<LoginPage />} />
        <Route path="/calendar" element={<div>calendar-placeholder</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("LoginPage", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("送信すると apiFetch が正しいエンドポイント・ボディで呼ばれる", async () => {
    const apiFetchSpy = vi.spyOn(apiClient, "apiFetch").mockResolvedValue({
      user: { id: 1, employee_id: "user001", name: "一般花子", role: "general" },
    });

    renderLoginPage();
    const user = userEvent.setup();

    await user.type(screen.getByLabelText("社員ID"), "user001");
    await user.type(screen.getByLabelText("パスワード"), "TestPassw0rd!");
    await user.click(screen.getByRole("button", { name: "ログイン" }));

    await waitFor(() => {
      expect(apiFetchSpy).toHaveBeenCalledWith(
        "/api/auth/login",
        expect.objectContaining({
          method: "POST",
          body: JSON.stringify({ employee_id: "user001", password: "TestPassw0rd!" }),
        }),
      );
    });
  });

  it("未入力のまま送信するとAPI呼び出し無しでエラーメッセージが表示される", async () => {
    const apiFetchSpy = vi.spyOn(apiClient, "apiFetch");

    renderLoginPage();
    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: "ログイン" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("社員IDを入力してください");
    expect(apiFetchSpy).not.toHaveBeenCalled();
  });

  it("APIが401を返すと「社員IDまたはパスワードが正しくありません」が表示される", async () => {
    vi.spyOn(apiClient, "apiFetch").mockRejectedValue(
      new apiClient.ApiError(401, { error_code: "AUTH_FAILED", message: "社員IDまたはパスワードが正しくありません" }),
    );

    renderLoginPage();
    const user = userEvent.setup();
    await user.type(screen.getByLabelText("社員ID"), "user001");
    await user.type(screen.getByLabelText("パスワード"), "WrongPassword1");
    await user.click(screen.getByRole("button", { name: "ログイン" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "社員IDまたはパスワードが正しくありません",
    );
  });
});
