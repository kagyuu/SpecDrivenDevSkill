// S07 ユーザー管理画面(管理者用)。docs/P002-frontend-spec.md §3 S07。
import { useEffect, useState, type FormEvent } from "react";
import { apiFetch } from "../api/client";
import { createUser, deactivateUser, fetchUsers, type AppUser } from "../api/users";

interface Me {
  id: number;
  employee_id: string;
  name: string;
  role: string;
}

export function UserAdminPage() {
  const [me, setMe] = useState<Me | null>(null);
  const [users, setUsers] = useState<AppUser[]>([]);
  const [employeeId, setEmployeeId] = useState("");
  const [name, setName] = useState("");
  const [role, setRole] = useState<"general" | "admin">("general");
  const [initialPassword, setInitialPassword] = useState("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    apiFetch<Me>("/api/me").then(setMe);
  }, []);

  function reload() {
    fetchUsers().then(setUsers);
  }

  useEffect(() => {
    if (me?.role === "admin") {
      reload();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [me]);

  if (!me) {
    return <main>読み込み中...</main>;
  }

  if (me.role !== "admin") {
    return <main>この画面を表示する権限がありません。</main>;
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setErrorMessage(null);
    try {
      await createUser({ employee_id: employeeId, name, role, initial_password: initialPassword });
      setEmployeeId("");
      setName("");
      setRole("general");
      setInitialPassword("");
      reload();
    } catch {
      setErrorMessage("この社員IDは既に登録されています");
    }
  }

  async function handleDelete(user: AppUser) {
    if (user.id === me!.id) {
      return; // 自分自身は無効化不可(ボタンは disabled にしているため通常到達しない)
    }
    if (!window.confirm(`ユーザー「${user.name}」を無効化しますか?`)) {
      return;
    }
    await deactivateUser(user.id);
    reload();
  }

  return (
    <main>
      <h1>ユーザー管理</h1>
      <table>
        <thead>
          <tr>
            <th>社員ID</th>
            <th>氏名</th>
            <th>権限</th>
            <th>状態</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          {users.map((user) => (
            <tr key={user.id}>
              <td>{user.employee_id}</td>
              <td>{user.name}</td>
              <td>{user.role === "admin" ? "管理者" : "一般"}</td>
              <td>{user.is_active ? "有効" : "無効"}</td>
              <td>
                {user.is_active && (
                  <button type="button" disabled={user.id === me.id} onClick={() => handleDelete(user)}>
                    削除
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <h2>新規登録</h2>
      <form onSubmit={handleSubmit}>
        <div>
          <label htmlFor="employee-id">社員ID</label>
          <input id="employee-id" value={employeeId} onChange={(e) => setEmployeeId(e.target.value)} required />
        </div>
        <div>
          <label htmlFor="user-name">氏名</label>
          <input id="user-name" value={name} onChange={(e) => setName(e.target.value)} required />
        </div>
        <div>
          <label htmlFor="user-role">権限</label>
          <select id="user-role" value={role} onChange={(e) => setRole(e.target.value as "general" | "admin")}>
            <option value="general">一般</option>
            <option value="admin">管理者</option>
          </select>
        </div>
        <div>
          <label htmlFor="initial-password">初期パスワード</label>
          <input
            id="initial-password"
            type="password"
            value={initialPassword}
            onChange={(e) => setInitialPassword(e.target.value)}
            minLength={8}
            required
          />
        </div>
        {errorMessage && <p role="alert">{errorMessage}</p>}
        <button type="submit">登録</button>
      </form>
    </main>
  );
}
