import { useState, type SubmitEvent } from "react";
import { Link } from "react-router";
import { updateMyProfile } from "../api/profiles";
import { useAuth } from "../auth/useAuth";
import { PrimaryButton, SECONDARY_CLASS } from "../components/Button";
import { ErrorMessage } from "../components/ErrorMessage";
import { CausesField, PhoneField, PostalCodeField } from "../components/ProfileFields";
import { Section } from "../components/Section";
import { TextField } from "../components/TextField";
import { formatPostalCode, joinPhone, splitPhone } from "../format";
import { useAction } from "../hooks/useAction";
import { routes } from "../routes";
import type { Profile } from "../types/user";

export const SAVED_CLASS =
  "block rounded-lg border border-emerald-200 bg-emerald-50 p-4 text-emerald-800";

export function ProfileForm({ user }: Readonly<{ user: Profile }>) {
  const { setUser } = useAuth();
  const { errorMessage, pending, run } = useAction();
  const [name, setName] = useState(user.name);
  const [phone, setPhone] = useState(splitPhone(user.phone ?? ""));
  const [postalCode, setPostalCode] = useState(formatPostalCode(user.postal_code ?? ""));
  const [preferredCauses, setPreferredCauses] = useState(user.preferred_causes ?? []);
  const [saved, setSaved] = useState(false);
  const isDonor = user.role === "donor";

  function handleSubmit(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault();
    const donorChanges = isDonor
      ? { postal_code: formatPostalCode(postalCode), preferred_causes: preferredCauses }
      : {};
    setSaved(false);
    // An empty phone removes the saved one, while null would keep it.
    run(() =>
      updateMyProfile({ name, phone: joinPhone(phone) ?? "", ...donorChanges }).then((profile) => {
        // A save answered after a logout must not log the user back in.
        setUser((current) => current && profile);
        setSaved(true);
      }),
    );
  }

  return (
    <form
      onSubmit={handleSubmit}
      onChange={() => setSaved(false)}
      className="divide-y divide-slate-200 border-t border-slate-200"
    >
      <Section title="Dados pessoais">
        <TextField
          label="Nome completo"
          autoComplete="name"
          value={name}
          onChange={(event) => setName(event.target.value)}
        />
        <PhoneField value={phone} onChange={setPhone} />
      </Section>
      {isDonor && (
        <Section title="Localização e causas">
          <PostalCodeField value={postalCode} onChange={setPostalCode} />
          <div className="sm:col-span-2">
            <CausesField value={preferredCauses} onChange={setPreferredCauses} />
          </div>
        </Section>
      )}
      <div className="space-y-4 pt-6">
        {errorMessage && <ErrorMessage message={errorMessage} />}
        {saved && <output className={SAVED_CLASS}>Perfil atualizado.</output>}
        <div className="flex justify-end gap-3">
          <Link to={routes.dashboard} className={`${SECONDARY_CLASS} flex items-center`}>
            Cancelar
          </Link>
          <PrimaryButton disabled={pending}>Salvar</PrimaryButton>
        </div>
      </div>
    </form>
  );
}
