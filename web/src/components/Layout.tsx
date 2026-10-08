import { Link, Outlet } from "react-router";
import { routes } from "../routes";

export function Layout() {
  return (
    <div className="min-h-screen bg-slate-50 text-slate-800">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto max-w-3xl p-4">
          <Link to={routes.dashboard} className="text-xl font-bold text-emerald-700">
            DonaBe
          </Link>
        </div>
      </header>
      <main className="mx-auto max-w-3xl p-4">
        <Outlet />
      </main>
    </div>
  );
}
