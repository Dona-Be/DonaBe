import { useState } from "react";
import { logout } from "../api/auth";
import { useAuth } from "../auth/useAuth";
import { Button } from "../components/Button";
import { ErrorMessage } from "../components/ErrorMessage";
import { friendlyMessage } from "../errors";
import type { Role } from "../types/user";

const roleLabels: Record<Role, string> = {
  donor: "Doador",
  manager: "Gestor de instituição",
};

export function Dashboard() {
  const { user, setUser } = useAuth();
  const [loggingOut, setLoggingOut] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  if (!user) return null;

  function handleLogout() {
    setLoggingOut(true);
    setErrorMessage(null);
    logout()
      .then(() => setUser(null))
      .catch((error: unknown) => setErrorMessage(friendlyMessage(error)))
      .finally(() => setLoggingOut(false));
  }

  return (
    <section className="mx-auto max-w-md space-y-4 rounded border border-slate-200 bg-white p-6">
      <h1 className="text-2xl font-semibold">Olá, {user.name}</h1>
      <p className="text-slate-600">Este é o seu painel. As funcionalidades vão aparecer aqui.</p>
      <div className="flex items-center gap-3">
        {user.picture_url && (
          <img src={user.picture_url} alt="" referrerPolicy="no-referrer" className="h-12 w-12 rounded-full" />
        )}
        <dl className="text-sm">
          <dt className="text-slate-500">E-mail</dt>
          <dd>{user.email}</dd>
          <dt className="mt-2 text-slate-500">Papel</dt>
          <dd>{roleLabels[user.role]}</dd>
        </dl>
      </div>
      <Button disabled={loggingOut} onClick={handleLogout}>
        Sair
      </Button>
      {errorMessage && <ErrorMessage message={errorMessage} />}
    </section>
  );
}
