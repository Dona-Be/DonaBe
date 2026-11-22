import { Navigate, Route, Routes } from "react-router";
import { GuestRoute } from "./auth/GuestRoute";
import { ProtectedRoute } from "./auth/ProtectedRoute";
import { Layout } from "./components/Layout";
import { Dashboard } from "./pages/Dashboard";
import { Login } from "./pages/Login";
import { MyProfile } from "./pages/MyProfile";
import { MyInstitutions } from "./pages/MyInstitutions";
import { InstitutionForm } from "./pages/InstitutionForm";
import { EditInstitution } from "./pages/EditInstitution";
import { routes } from "./routes";

export function App() {
  return (
    <Routes>
      <Route element={<ProtectedRoute />}>
        <Route element={<Layout />}>
          <Route path={routes.dashboard} element={<Dashboard />} />
          <Route path={routes.profile} element={<MyProfile />} />
          <Route element={<ProtectedRoute only="manager" />}>
            <Route path={routes.institutions} element={<MyInstitutions />} />
            <Route path={routes.newInstitution} element={<InstitutionForm />} />
            <Route path={`${routes.institutions}/:id/editar`} element={<EditInstitution />} />
          </Route>
        </Route>
      </Route>
      <Route element={<GuestRoute />}>
        <Route path={routes.login} element={<Login />} />
      </Route>
      <Route path="*" element={<Navigate to={routes.dashboard} replace />} />
    </Routes>
  );
}
