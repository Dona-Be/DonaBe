import { Navigate, Route, Routes } from "react-router";
import { GuestRoute } from "./auth/GuestRoute";
import { ProtectedRoute } from "./auth/ProtectedRoute";
import { Layout } from "./components/Layout";
import { Dashboard } from "./pages/Dashboard";
import { Login } from "./pages/Login";
import { routes } from "./routes";

export function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route element={<ProtectedRoute />}>
          <Route path={routes.dashboard} element={<Dashboard />} />
        </Route>
        <Route element={<GuestRoute />}>
          <Route path={routes.login} element={<Login />} />
        </Route>
        <Route path="*" element={<Navigate to={routes.dashboard} replace />} />
      </Route>
    </Routes>
  );
}
