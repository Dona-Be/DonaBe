import { useState, type SubmitEvent } from "react";
import { createDonor } from "../api/profiles";
import { useAuth } from "../auth/useAuth";
import { causeLabels, causes, type Cause } from "../causes";
import { AuthLayout } from "../components/AuthLayout";
import { PrimaryButton, SecondaryButton } from "../components/Button";
import { ErrorMessage } from "../components/ErrorMessage";
import { TextField } from "../components/TextField";
import { useAction } from "../hooks/useAction";

const CAUSE_CLASS =
  "cursor-pointer rounded-full border border-slate-500 px-4 py-2 has-checked:border-sky-700 " +
  "has-checked:bg-sky-100 has-checked:ring-1 has-checked:ring-sky-700 " +
  "has-focus-visible:outline-2 has-focus-visible:outline-offset-2 " +
  "has-focus-visible:outline-sky-700";

export function DonorForm({ onBack }: Readonly<{ onBack: () => void }>) {
  const { setUser } = useAuth();
  const { errorMessage, pending, run } = useAction();
  const [postalCode, setPostalCode] = useState("");
  const [phone, setPhone] = useState("");
  const [preferredCauses, setPreferredCauses] = useState<Cause[]>([]);

  function toggle(cause: Cause) {
    const others = preferredCauses.filter((preferred) => preferred !== cause);
    setPreferredCauses(others.length < preferredCauses.length ? others : [...others, cause]);
  }

  function handleSubmit(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault();
    const donor = {
      postal_code: postalCode,
      phone: phone || null,
      preferred_causes: preferredCauses,
    };
    run(() => createDonor(donor).then(setUser));
  }

  return (
    <AuthLayout title="Local e Contato">
      <form onSubmit={handleSubmit} className="space-y-6">
        <TextField
          label="CEP"
          hint="Usamos o CEP para mostrar instituições perto de você."
          inputMode="numeric"
          autoComplete="postal-code"
          value={postalCode}
          onChange={(event) => setPostalCode(event.target.value)}
        />
        <TextField
          label="Telefone"
          optional
          hint="Com DDD, por exemplo (11) 99999-0000."
          type="tel"
          autoComplete="tel-national"
          value={phone}
          onChange={(event) => setPhone(event.target.value)}
        />
        <fieldset>
          <legend className="mb-2 font-bold">
            Causas preferidas<span className="font-normal"> (escolha quantas quiser)</span>
          </legend>
          <div className="flex flex-wrap gap-2">
            {causes.map((cause) => (
              <label key={cause} className={CAUSE_CLASS}>
                <input
                  type="checkbox"
                  className="sr-only"
                  checked={preferredCauses.includes(cause)}
                  onChange={() => toggle(cause)}
                />
                {causeLabels[cause]}
              </label>
            ))}
          </div>
        </fieldset>
        {errorMessage && <ErrorMessage message={errorMessage} />}
        <div className="flex gap-3">
          <SecondaryButton disabled={pending} onClick={onBack}>
            Voltar
          </SecondaryButton>
          <PrimaryButton disabled={pending} className="flex-1">
            Concluir cadastro
          </PrimaryButton>
        </div>
      </form>
    </AuthLayout>
  );
}
