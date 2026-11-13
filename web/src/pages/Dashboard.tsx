import { logout } from "../api/auth";
import { useAuth } from "../auth/useAuth";
import { SecondaryButton } from "../components/Button";
import { ErrorMessage } from "../components/ErrorMessage";
import { useAction } from "../hooks/useAction";
import type { Role } from "../types/user";

const roleLabels: Record<Role, string> = {
  donor: "Doador",
  manager: "Gestor de instituição",
};

export function Dashboard() {
  const { user, role, setUser } = useAuth();
  const { errorMessage, pending, run } = useAction();

  if (!user || !role) return null;

  return (
    <section className="mx-auto max-w-md space-y-4 rounded border border-slate-200 bg-white p-6">
      <h1 className="text-2xl font-semibold">Olá, {user.name}</h1>
      <p className="text-slate-600">Este é o seu painel. As funcionalidades vão aparecer aqui.</p>
      <div className="flex items-center gap-3">
        {user.picture_url && (
          <img
            src={user.picture_url}
            alt=""
            referrerPolicy="no-referrer"
            className="h-12 w-12 rounded-full"
          />
        )}
        <dl className="text-sm">
          <dt className="text-slate-500">E-mail</dt>
          <dd>{user.email}</dd>
          <dt className="mt-2 text-slate-500">Papel</dt>
          <dd>{roleLabels[role]}</dd>
        </dl>
      </div>
      <SecondaryButton
        disabled={pending}
        onClick={() => run(() => logout().then(() => setUser(null)))}
      >
        Sair de todos os aparelhos
      </SecondaryButton>
      {errorMessage && <ErrorMessage message={errorMessage} />}
    </section>
  );
}
