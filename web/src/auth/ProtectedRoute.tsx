import { Navigate, Outlet } from "react-router";
import { Loading } from "../components/Loading";
import { routes } from "../routes";
import { useAuth } from "./useAuth";

export function ProtectedRoute() {
  const { user, loading } = useAuth();

  if (loading) return <Loading />;
  if (!user) return <Navigate to={routes.login} replace />;

  return <Outlet />;
}
