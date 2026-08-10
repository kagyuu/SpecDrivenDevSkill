// U005-T3 (docs/P007-impl-direction/U005-user-management-and-hardening.md):
// S07ユーザー管理画面 (docs/P002-frontend-spec.md 3.7節)。
// ★U005-T4改訂: 共通Headerコンポーネントを追加した(この画面はU005-T3時点では
// ヘッダーを持っていなかった)。
import { useEffect, useState, type FormEvent } from 'react'

import { authApi, type CurrentUser } from '../api/authApi'
import { userApi, UserApiError, type ManagedUser, type Role } from '../api/userApi'
import { Header } from '../components/Header'

const NAME_MAX_LENGTH = 50
const PASSWORD_MIN_LENGTH = 8

interface FormState {
  employeeId: string
  name: string
  password: string
  role: Role
  isActive: boolean
}

const EMPTY_FORM: FormState = {
  employeeId: '',
  name: '',
  password: '',
  role: 'general',
  isActive: true,
}

interface FormErrors {
  employeeId?: string
  name?: string
  password?: string
}

// docs/P002-frontend-spec.md 3.7節: サーバーのエラーコードをメッセージに
// マッピングする(この画面の実装内容として明記されている)。
const ERROR_CODE_MESSAGES: Record<string, string> = {
  SELF_DEACTIVATION_FORBIDDEN: '自分自身は無効化できません',
  LAST_ADMIN_PROTECTED: '最後の管理者アカウントは無効化できません',
}

function Forbidden() {
  return (
    <div>
      <p>アクセス権がありません。</p>
      <a href="/">トップに戻る</a>
    </div>
  )
}

export function UserManagementPage() {
  const [authState, setAuthState] = useState<'loading' | 'admin' | 'forbidden'>('loading')
  const [users, setUsers] = useState<ManagedUser[]>([])
  const [loadError, setLoadError] = useState<string | null>(null)
  const [form, setForm] = useState<FormState>(EMPTY_FORM)
  const [errors, setErrors] = useState<FormErrors>({})
  const [formMessage, setFormMessage] = useState<string | null>(null)
  const [editingEmployeeId, setEditingEmployeeId] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    authApi
      .getMe()
      .then((user: CurrentUser) => {
        if (!cancelled) setAuthState(user.role === 'admin' ? 'admin' : 'forbidden')
      })
      .catch(() => {
        if (!cancelled) setAuthState('forbidden')
      })
    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    if (authState !== 'admin') return
    userApi
      .listUsers(true)
      .then(setUsers)
      .catch(() => setLoadError('ユーザー一覧の取得に失敗しました'))
  }, [authState])

  function startEdit(user: ManagedUser) {
    setEditingEmployeeId(user.employee_id)
    setForm({
      employeeId: user.employee_id,
      name: user.name,
      password: '',
      role: user.role,
      isActive: user.is_active,
    })
    setErrors({})
    setFormMessage(null)
  }

  function resetForm() {
    setEditingEmployeeId(null)
    setForm(EMPTY_FORM)
    setErrors({})
    setFormMessage(null)
  }

  function validate(): FormErrors {
    const errors: FormErrors = {}
    if (editingEmployeeId === null && !form.employeeId.trim()) {
      errors.employeeId = '社員IDを入力してください'
    }
    if (!form.name.trim()) {
      errors.name = '氏名を入力してください'
    } else if (form.name.length > NAME_MAX_LENGTH) {
      errors.name = '氏名は50文字以内で入力してください'
    }
    const passwordRequired = editingEmployeeId === null
    if (passwordRequired && form.password.length < PASSWORD_MIN_LENGTH) {
      errors.password = 'パスワードは8文字以上で入力してください'
    } else if (form.password && form.password.length < PASSWORD_MIN_LENGTH) {
      errors.password = 'パスワードは8文字以上で入力してください'
    }
    return errors
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setFormMessage(null)
    const validationErrors = validate()
    setErrors(validationErrors)
    if (Object.keys(validationErrors).length > 0) {
      return
    }

    try {
      if (editingEmployeeId === null) {
        const created = await userApi.createUser({
          employee_id: form.employeeId,
          name: form.name,
          password: form.password,
          role: form.role,
        })
        setUsers((prev) => [...prev, created])
      } else {
        const updated = await userApi.updateUser(editingEmployeeId, {
          name: form.name,
          password: form.password.trim() === '' ? null : form.password,
          role: form.role,
          is_active: form.isActive,
        })
        setUsers((prev) => prev.map((user) => (user.employee_id === updated.employee_id ? updated : user)))
      }
      resetForm()
    } catch (error) {
      if (error instanceof UserApiError && error.fields) {
        setErrors(error.fields as FormErrors)
        return
      }
      if (error instanceof UserApiError && ERROR_CODE_MESSAGES[error.code]) {
        setFormMessage(ERROR_CODE_MESSAGES[error.code])
        return
      }
      setFormMessage('保存に失敗しました')
    }
  }

  async function handleDelete(user: ManagedUser) {
    if (!window.confirm('このユーザーを無効化しますか?')) {
      return
    }
    try {
      const result = await userApi.deleteUser(user.employee_id)
      setUsers((prev) =>
        prev.map((item) =>
          item.employee_id === result.employee_id ? { ...item, is_active: result.is_active } : item,
        ),
      )
    } catch (error) {
      if (error instanceof UserApiError && ERROR_CODE_MESSAGES[error.code]) {
        setFormMessage(ERROR_CODE_MESSAGES[error.code])
        return
      }
      setFormMessage('無効化に失敗しました')
    }
  }

  if (authState === 'loading') {
    return null
  }
  if (authState === 'forbidden') {
    return <Forbidden />
  }

  return (
    <div>
      <Header currentScreen="S07" />

      <h1>ユーザー管理</h1>
      {loadError && <p role="alert">{loadError}</p>}
      {formMessage && <p role="alert">{formMessage}</p>}

      <table>
        <thead>
          <tr>
            <th>社員ID</th>
            <th>氏名</th>
            <th>権限</th>
            <th>有効</th>
            <th />
          </tr>
        </thead>
        <tbody>
          {users.map((user) => (
            <tr key={user.employee_id}>
              <td>{user.employee_id}</td>
              <td>{user.name}</td>
              <td>{user.role === 'admin' ? '管理者' : '一般'}</td>
              <td>{user.is_active ? '有効' : '無効'}</td>
              <td>
                <button type="button" onClick={() => startEdit(user)}>
                  編集
                </button>
                <button type="button" onClick={() => handleDelete(user)}>
                  削除
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <form onSubmit={handleSubmit} aria-label={editingEmployeeId === null ? 'ユーザー登録フォーム' : 'ユーザー編集フォーム'}>
        <h2>{editingEmployeeId === null ? '新規登録' : '編集'}</h2>

        <label htmlFor="user-employee-id">社員ID</label>
        <input
          id="user-employee-id"
          value={form.employeeId}
          disabled={editingEmployeeId !== null}
          onChange={(event) => setForm((prev) => ({ ...prev, employeeId: event.target.value }))}
        />
        {errors.employeeId && <p role="alert">{errors.employeeId}</p>}

        <label htmlFor="user-name">氏名</label>
        <input
          id="user-name"
          value={form.name}
          onChange={(event) => setForm((prev) => ({ ...prev, name: event.target.value }))}
        />
        {errors.name && <p role="alert">{errors.name}</p>}

        <label htmlFor="user-password">パスワード</label>
        <input
          id="user-password"
          type="password"
          value={form.password}
          onChange={(event) => setForm((prev) => ({ ...prev, password: event.target.value }))}
        />
        {errors.password && <p role="alert">{errors.password}</p>}

        <label htmlFor="user-role">権限</label>
        <select
          id="user-role"
          value={form.role}
          onChange={(event) => setForm((prev) => ({ ...prev, role: event.target.value as Role }))}
        >
          <option value="general">一般</option>
          <option value="admin">管理者</option>
        </select>

        {editingEmployeeId !== null && (
          <label htmlFor="user-is-active">
            <input
              id="user-is-active"
              type="checkbox"
              checked={form.isActive}
              onChange={(event) => setForm((prev) => ({ ...prev, isActive: event.target.checked }))}
            />
            有効
          </label>
        )}

        <button type="submit">{editingEmployeeId === null ? '登録' : '更新'}</button>
        {editingEmployeeId !== null && (
          <button type="button" onClick={resetForm}>
            キャンセル
          </button>
        )}
      </form>
    </div>
  )
}

export default UserManagementPage
