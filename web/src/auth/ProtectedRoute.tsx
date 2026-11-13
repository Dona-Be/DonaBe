import { Navigate, Outlet } from "react-router";
import { Loading } from "../components/Loading";
import { ProfileSetup } from "../pages/ProfileSetup";
import { routes } from "../routes";
import type { Role } from "../types/user";
import { useAuth } from "./useAuth";

export function ProtectedRoute({ only }: Readonly<{ only?: Role }>) {
  const { user, role, loading } = useAuth();

  if (loading) return <Loading />;
  if (!user) return <Navigate to={routes.login} replace />;
  if (!role) return <ProfileSetup />;
  if (only && only !== role) return <Navigate to={routes.dashboard} replace />;

  return <Outlet />;
}
