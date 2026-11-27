import { Link, Outlet } from "react-router";
import { logout } from "../api/auth";
import { useAuth } from "../auth/useAuth";
import { useAction } from "../hooks/useAction";
import { routes } from "../routes";
import { ErrorMessage } from "./ErrorMessage";
import { Logo } from "./Logo";
import { NotificationBell } from "./NotificationBell";

export function Layout() {
  const { role, setUser } = useAuth();
  const { errorMessage, pending, run } = useAction();

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-3xl flex-wrap items-center justify-between gap-2 p-4">
          <Link to={routes.dashboard} className="text-xl">
            <Logo />
          </Link>
          <div className="flex items-center gap-3">
            <nav className="flex gap-3">
              <Link to={routes.dashboard} className="hover:underline">
                Início
              </Link>
              <span aria-hidden="true">|</span>
              <Link to={routes.profile} className="hover:underline">
                Meu perfil
              </Link>
              {role === "manager" && (
                <>
                  <span aria-hidden="true">|</span>
                  <Link to={routes.institutions} className="hover:underline">
                    Minhas instituições
                  </Link>
                </>
              )}
              <span aria-hidden="true">|</span>
              <button
                type="button"
                disabled={pending}
                onClick={() => run(() => logout().then(() => setUser(null)))}
                className="cursor-pointer hover:underline"
              >
                Sair
              </button>
            </nav>
            <NotificationBell />
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-3xl space-y-4 p-4">
        {errorMessage && <ErrorMessage message={errorMessage} />}
        <Outlet />
      </main>
    </div>
  );
}
