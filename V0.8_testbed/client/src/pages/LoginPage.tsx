// U001-T5 (docs/P007-impl-direction/U001-foundation-and-auth.md): S01ログイン
// 画面 (docs/P002-frontend-spec.md 3.1節)。
import { useEffect, useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'

import { authApi } from '../api/authApi'

export function LoginPage() {
  const navigate = useNavigate()
  const [employeeId, setEmployeeId] = useState('')
  const [password, setPassword] = useState('')
  const [employeeIdError, setEmployeeIdError] = useState<string | null>(null)
  const [passwordError, setPasswordError] = useState<string | null>(null)
  const [formError, setFormError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    // docs/P002-frontend-spec.md 3.1節 動作4:
    // 「ログイン済み状態でS01に直接アクセスした場合は、S02へリダイレクトする」。
    // S02(カレンダー画面)自体はU003の範囲だが、その遷移先である "/" は
    // U001-T5時点で既にプレースホルダとして存在する(App.tsx参照)ため、
    // 遷移先として使える。
    let cancelled = false
    authApi
      .getMe()
      .then(() => {
        if (!cancelled) {
          navigate('/', { replace: true })
        }
      })
      .catch(() => {
        // 未ログイン状態。ログイン画面をそのまま表示する。
      })
    return () => {
      cancelled = true
    }
  }, [navigate])

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setFormError(null)

    const trimmedEmployeeId = employeeId.trim()
    const nextEmployeeIdError = trimmedEmployeeId ? null : '社員IDを入力してください'
    const nextPasswordError = password ? null : 'パスワードを入力してください'
    setEmployeeIdError(nextEmployeeIdError)
    setPasswordError(nextPasswordError)
    if (nextEmployeeIdError || nextPasswordError) {
      return
    }

    setSubmitting(true)
    try {
      await authApi.login(employeeId, password)
      navigate('/')
    } catch {
      // docs/P002-frontend-spec.md 3.1節: 社員IDが存在しない場合とパスワードが
      // 誤っている場合を区別するメッセージは出さない(アカウント列挙対策)。
      setFormError('社員IDまたはパスワードが正しくありません')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} aria-label="ログインフォーム">
      <h1>ログイン</h1>

      <label htmlFor="employee-id">社員ID</label>
      <input
        id="employee-id"
        name="employeeId"
        type="text"
        value={employeeId}
        onChange={(event) => setEmployeeId(event.target.value)}
      />
      {employeeIdError && <p role="alert">{employeeIdError}</p>}

      <label htmlFor="password">パスワード</label>
      <input
        id="password"
        name="password"
        type="password"
        value={password}
        onChange={(event) => setPassword(event.target.value)}
      />
      {passwordError && <p role="alert">{passwordError}</p>}

      {formError && <p role="alert">{formError}</p>}

      <button type="submit" disabled={submitting}>
        ログイン
      </button>
    </form>
  )
}

export default LoginPage
