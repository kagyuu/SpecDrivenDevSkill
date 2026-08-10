// U002-T3 (docs/P007-impl-direction/U002-room-management.md): S06会議室管理
// 画面 (docs/P002-frontend-spec.md 3.6節)。
// ★U005-T4改訂: 共通Headerコンポーネントを追加した(この画面はU002-T3時点では
// ヘッダーを持っていなかった)。
import { useEffect, useState, type FormEvent } from 'react'

import { authApi, type CurrentUser } from '../api/authApi'
import { roomApi, type Room } from '../api/roomApi'
import { Header } from '../components/Header'

// docs/P002-frontend-spec.md 3.6節: 設備は固定の選択式チェックボックス群。
const EQUIPMENT_OPTIONS = ['プロジェクター', 'ホワイトボード', 'Web会議設備', '電話会議設備']

const NAME_MAX_LENGTH = 50
const DESCRIPTION_MAX_LENGTH = 200

interface FormState {
  name: string
  capacity: string
  equipment: string[]
  description: string
  isActive: boolean
}

const EMPTY_FORM: FormState = {
  name: '',
  capacity: '',
  equipment: [],
  description: '',
  isActive: true,
}

interface FormErrors {
  name?: string
  capacity?: string
  description?: string
}

function validate(form: FormState): FormErrors {
  const errors: FormErrors = {}
  if (!form.name.trim()) {
    errors.name = '会議室名を入力してください'
  } else if (form.name.length > NAME_MAX_LENGTH) {
    errors.name = '会議室名は50文字以内で入力してください'
  }

  const capacityNumber = Number(form.capacity)
  if (form.capacity.trim() === '' || !Number.isInteger(capacityNumber) || capacityNumber < 1) {
    errors.capacity = '収容人数は1以上の整数で入力してください'
  }

  if (form.description.length > DESCRIPTION_MAX_LENGTH) {
    errors.description = '説明文は200文字以内で入力してください'
  }

  return errors
}

function Forbidden() {
  return (
    <div>
      <p>アクセス権がありません。</p>
      <a href="/">トップに戻る</a>
    </div>
  )
}

export function RoomManagementPage() {
  const [authState, setAuthState] = useState<'loading' | 'admin' | 'forbidden'>('loading')
  const [rooms, setRooms] = useState<Room[]>([])
  const [loadError, setLoadError] = useState<string | null>(null)
  const [form, setForm] = useState<FormState>(EMPTY_FORM)
  const [errors, setErrors] = useState<FormErrors>({})
  const [editingRoomId, setEditingRoomId] = useState<number | null>(null)

  useEffect(() => {
    let cancelled = false
    authApi
      .getMe()
      .then((user: CurrentUser) => {
        if (cancelled) return
        setAuthState(user.role === 'admin' ? 'admin' : 'forbidden')
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
    let cancelled = false
    roomApi
      .listRooms(true)
      .then((result) => {
        if (!cancelled) setRooms(result)
      })
      .catch(() => {
        if (!cancelled) setLoadError('会議室一覧の取得に失敗しました')
      })
    return () => {
      cancelled = true
    }
  }, [authState])

  function startEdit(room: Room) {
    setEditingRoomId(room.room_id)
    setForm({
      name: room.name,
      capacity: String(room.capacity),
      equipment: room.equipment,
      description: room.description ?? '',
      isActive: room.is_active,
    })
    setErrors({})
  }

  function resetForm() {
    setEditingRoomId(null)
    setForm(EMPTY_FORM)
    setErrors({})
  }

  function toggleEquipment(name: string) {
    setForm((prev) => ({
      ...prev,
      equipment: prev.equipment.includes(name)
        ? prev.equipment.filter((item) => item !== name)
        : [...prev.equipment, name],
    }))
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const validationErrors = validate(form)
    setErrors(validationErrors)
    if (Object.keys(validationErrors).length > 0) {
      return
    }

    const input = {
      name: form.name,
      capacity: Number(form.capacity),
      equipment: form.equipment,
      description: form.description || null,
    }

    const saved =
      editingRoomId === null
        ? await roomApi.createRoom(input)
        : await roomApi.updateRoom(editingRoomId, { ...input, is_active: form.isActive })

    setRooms((prev) => {
      if (editingRoomId === null) return [...prev, saved]
      return prev.map((room) => (room.room_id === saved.room_id ? saved : room))
    })
    resetForm()
  }

  async function handleDelete(room: Room) {
    if (!window.confirm('この会議室を無効化しますか?')) {
      return
    }
    const result = await roomApi.deleteRoom(room.room_id)
    setRooms((prev) =>
      prev.map((item) => (item.room_id === result.room_id ? { ...item, is_active: result.is_active } : item)),
    )
  }

  if (authState === 'loading') {
    return null
  }
  if (authState === 'forbidden') {
    return <Forbidden />
  }

  return (
    <div>
      <Header currentScreen="S06" />

      <h1>会議室管理</h1>
      {loadError && <p role="alert">{loadError}</p>}

      <table>
        <thead>
          <tr>
            <th>名前</th>
            <th>収容人数</th>
            <th>設備</th>
            <th>説明文</th>
            <th>有効</th>
            <th />
          </tr>
        </thead>
        <tbody>
          {rooms.map((room) => (
            <tr key={room.room_id}>
              <td>{room.name}</td>
              <td>{room.capacity}</td>
              <td>{room.equipment.join('、')}</td>
              <td>{room.description ?? ''}</td>
              <td>{room.is_active ? '有効' : '無効'}</td>
              <td>
                <button type="button" onClick={() => startEdit(room)}>
                  編集
                </button>
                <button type="button" onClick={() => handleDelete(room)}>
                  削除
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <form onSubmit={handleSubmit} aria-label={editingRoomId === null ? '会議室登録フォーム' : '会議室編集フォーム'}>
        <h2>{editingRoomId === null ? '新規登録' : '編集'}</h2>

        <label htmlFor="room-name">会議室名</label>
        <input
          id="room-name"
          value={form.name}
          onChange={(event) => setForm((prev) => ({ ...prev, name: event.target.value }))}
        />
        {errors.name && <p role="alert">{errors.name}</p>}

        <label htmlFor="room-capacity">収容人数</label>
        <input
          id="room-capacity"
          type="number"
          value={form.capacity}
          onChange={(event) => setForm((prev) => ({ ...prev, capacity: event.target.value }))}
        />
        {errors.capacity && <p role="alert">{errors.capacity}</p>}

        <fieldset>
          <legend>設備</legend>
          {EQUIPMENT_OPTIONS.map((option) => (
            <label key={option}>
              <input
                type="checkbox"
                checked={form.equipment.includes(option)}
                onChange={() => toggleEquipment(option)}
              />
              {option}
            </label>
          ))}
        </fieldset>

        <label htmlFor="room-description">説明文</label>
        <textarea
          id="room-description"
          value={form.description}
          onChange={(event) => setForm((prev) => ({ ...prev, description: event.target.value }))}
        />
        {errors.description && <p role="alert">{errors.description}</p>}

        <button type="submit">{editingRoomId === null ? '登録' : '更新'}</button>
        {editingRoomId !== null && (
          <button type="button" onClick={resetForm}>
            キャンセル
          </button>
        )}
      </form>
    </div>
  )
}

export default RoomManagementPage
