// ルーティング定義。docs/P002-frontend-spec.md §4(画面遷移図)。
// U004完了時点: S01〜S07すべて実ルート。
import { createBrowserRouter } from "react-router-dom";
import { CalendarPage } from "./pages/CalendarPage";
import { LoginPage } from "./pages/LoginPage";
import { MyReservationsPage } from "./pages/MyReservationsPage";
import { ReservationCreatePage } from "./pages/ReservationCreatePage";
import { ReservationDetailPage } from "./pages/ReservationDetailPage";
import { RoomAdminPage } from "./pages/RoomAdminPage";
import { UserAdminPage } from "./pages/UserAdminPage";

export const router = createBrowserRouter([
  { path: "/", element: <LoginPage /> },
  { path: "/calendar", element: <CalendarPage /> },
  { path: "/reservations/new", element: <ReservationCreatePage /> },
  { path: "/reservations/:id", element: <ReservationDetailPage /> },
  { path: "/my-reservations", element: <MyReservationsPage /> },
  { path: "/rooms", element: <RoomAdminPage /> },
  { path: "/users", element: <UserAdminPage /> },
]);
