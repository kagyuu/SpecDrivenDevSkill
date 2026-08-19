// S01 ログイン画面。docs/P002-frontend-spec.md §3 S01。
import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { apiFetch, ApiError } from "../api/client";

interface LoginResponseUser {
  id: number;
  employee_id: string;
  name: string;
  role: string;
}

interface LoginResponse {
  user: LoginResponseUser;
}

export function LoginPage() {
  const [employeeId, setEmployeeId] = useState("");
  const [password, setPassword] = useState("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const navigate = useNavigate();

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setErrorMessage(null);

    if (!employeeId) {
      setErrorMessage("社員IDを入力してください");
      return;
    }
    if (!password) {
      setErrorMessage("パスワードを入力してください");
      return;
    }

    setSubmitting(true);
    try {
      await apiFetch<LoginResponse>("/api/auth/login", {
        method: "POST",
        body: JSON.stringify({ employee_id: employeeId, password }),
      });
      navigate("/calendar");
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
        setErrorMessage("社員IDまたはパスワードが正しくありません");
      } else {
        setErrorMessage("ログインに失敗しました。時間をおいて再度お試しください。");
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main>
      <h1>ログイン</h1>
      <form onSubmit={handleSubmit}>
        <div>
          <label htmlFor="employeeId">社員ID</label>
          <input
            id="employeeId"
            name="employeeId"
            type="text"
            value={employeeId}
            onChange={(event) => setEmployeeId(event.target.value)}
          />
        </div>
        <div>
          <label htmlFor="password">パスワード</label>
          <input
            id="password"
            name="password"
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />
        </div>
        {errorMessage && <p role="alert">{errorMessage}</p>}
        <button type="submit" disabled={submitting}>
          ログイン
        </button>
      </form>
    </main>
  );
}
