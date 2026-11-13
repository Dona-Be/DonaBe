import { Link, Outlet } from "react-router";
import { routes } from "../routes";
import { Logo } from "./Logo";

export function Layout() {
  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto max-w-3xl p-4">
          <Link to={routes.dashboard} className="text-xl">
            <Logo />
          </Link>
        </div>
      </header>
      <main className="mx-auto max-w-3xl p-4">
        <Outlet />
      </main>
    </div>
  );
}
