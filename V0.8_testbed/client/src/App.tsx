// U001-T5 wires up react-router-dom and /login (S01). U002-T3 adds
// /admin/rooms (S06); RoomManagementPage itself performs the
// role=admin以外は403表示 access check (docs/P002-frontend-spec.md 3.6節), so
// this file just declares the route, matching how /login is declared.
// U003-T4 replaces the "/" placeholder with CalendarPage (S02, this task's
// own 実装内容: "ログイン後のルートをこのページに差し替える"). U003-T5 adds
// /reservations/new (S03). U004-T3 adds /reservations/:id (S04, connecting
// the routing scaffold U003-T4's CalendarPage already navigates to).
// U004-T4 adds /my-reservations (S05), connecting the header link
// CalendarPage already renders (`<a href="/my-reservations">`). U005-T3
// adds /admin/users (S07); like S06, UserManagementPage performs its own
// role=admin以外は403表示 access check.
import { BrowserRouter, Route, Routes } from 'react-router-dom'

import CalendarPage from './pages/CalendarPage'
import LoginPage from './pages/LoginPage'
import MyReservationsPage from './pages/MyReservationsPage'
import ReservationCreatePage from './pages/ReservationCreatePage'
import ReservationDetailPage from './pages/ReservationDetailPage'
import RoomManagementPage from './pages/RoomManagementPage'
import UserManagementPage from './pages/UserManagementPage'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/admin/rooms" element={<RoomManagementPage />} />
        <Route path="/admin/users" element={<UserManagementPage />} />
        <Route path="/reservations/new" element={<ReservationCreatePage />} />
        <Route path="/reservations/:id" element={<ReservationDetailPage />} />
        <Route path="/my-reservations" element={<MyReservationsPage />} />
        <Route path="/" element={<CalendarPage />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
