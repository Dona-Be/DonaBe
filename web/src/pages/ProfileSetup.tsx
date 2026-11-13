import { useState, type SubmitEvent } from "react";
import { logout } from "../api/auth";
import { createManager } from "../api/profiles";
import { useAuth } from "../auth/useAuth";
import { AuthLayout } from "../components/AuthLayout";
import { PrimaryButton, SecondaryButton } from "../components/Button";
import { ErrorMessage } from "../components/ErrorMessage";
import { useAction } from "../hooks/useAction";
import type { Role } from "../types/user";
import { DonorForm } from "./DonorForm";

const OPTION_CLASS =
  "flex h-20 cursor-pointer items-center rounded-xl border border-slate-500 px-6 text-xl " +
  "font-bold has-checked:border-sky-700 has-checked:bg-sky-100 has-checked:ring-1 " +
  "has-checked:ring-sky-700 has-focus-visible:outline-2 has-focus-visible:outline-offset-2 " +
  "has-focus-visible:outline-sky-700";

const OPTIONS: { role: Role; label: string }[] = [
  { role: "donor", label: "Quero doar" },
  { role: "manager", label: "Represento uma instituição" },
];

export function ProfileSetup() {
  const { setUser } = useAuth();
  const { errorMessage, setErrorMessage, pending, run } = useAction();
  const [role, setRole] = useState<Role>("donor");
  const [choosing, setChoosing] = useState(true);

  if (!choosing) return <DonorForm onBack={() => setChoosing(true)} />;

  function handleSubmit(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault();
    setErrorMessage(null);
    if (role === "donor") setChoosing(false);
    else run(() => createManager().then(setUser));
  }

  return (
    <AuthLayout title="Perfil">
      <form onSubmit={handleSubmit} className="space-y-6">
        <fieldset className="space-y-3">
          <legend className="sr-only">Como você vai usar o DonaBe?</legend>
          {OPTIONS.map((option) => (
            <label key={option.role} className={OPTION_CLASS}>
              <input
                type="radio"
                name="role"
                className="sr-only"
                checked={role === option.role}
                onChange={() => setRole(option.role)}
              />
              {option.label}
            </label>
          ))}
        </fieldset>
        <p className="text-slate-600">Esta escolha não pode ser alterada depois.</p>
        {errorMessage && <ErrorMessage message={errorMessage} />}
        <div className="flex gap-3">
          <SecondaryButton
            disabled={pending}
            onClick={() => run(() => logout().then(() => setUser(null)))}
          >
            Sair
          </SecondaryButton>
          <PrimaryButton disabled={pending} className="flex-1">
            Continuar
          </PrimaryButton>
        </div>
      </form>
    </AuthLayout>
  );
}
