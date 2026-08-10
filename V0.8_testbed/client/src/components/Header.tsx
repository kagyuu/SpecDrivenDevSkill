// U005-T4 (docs/P007-impl-direction/U005-user-management-and-hardening.md):
// 共通ヘッダーコンポーネント (docs/P002-frontend-spec.md 3.0節)。
//
// ★実施メモ: このタスクの【作成・編集対象ファイル】は CalendarPage(S02)/
// MyReservationsPage(S05)/RoomManagementPage(S06)/UserManagementPage(S07)の
// 4画面のみを列挙しており、S04(ReservationDetailPage.tsx)は含まれていない
// (currentScreen の型自体は3.0節に合わせて'S04'も許容する)。そのため
// ReservationDetailPage は今回このコンポーネントに置き換えていない。
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { authApi, type CurrentUser } from '../api/authApi'

export type ScreenName = 'S02' | 'S04' | 'S05' | 'S06' | 'S07'

export interface HeaderProps {
  currentScreen: ScreenName
}

export function Header({ currentScreen }: HeaderProps) {
  const navigate = useNavigate()
  const [user, setUser] = useState<CurrentUser | null>(null)

  useEffect(() => {
    authApi.getMe().then(setUser).catch(() => setUser(null))
  }, [])

  async function handleLogout() {
    await authApi.logout()
    navigate('/login')
  }

  const isAdmin = user?.role === 'admin'

  return (
    <header>
      {user && <span>{user.name}</span>}
      <a href="/my-reservations">マイ予約</a>
      {isAdmin && <a href="/admin/rooms">会議室管理</a>}
      {/* docs/P002-frontend-spec.md 3.0節: 「ユーザー管理」はS06画面表示中の
          管理者にのみ表示する(他画面では管理者であっても表示しない)。 */}
      {isAdmin && currentScreen === 'S06' && <a href="/admin/users">ユーザー管理</a>}
      <button type="button" onClick={handleLogout}>
        ログアウト
      </button>
    </header>
  )
}

export default Header
