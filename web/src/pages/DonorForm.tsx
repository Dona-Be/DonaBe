import { useState, type SubmitEvent } from "react";
import { createDonor } from "../api/profiles";
import { useAuth } from "../auth/useAuth";
import type { Cause } from "../causes";
import { AuthLayout } from "../components/AuthLayout";
import { PrimaryButton, SecondaryButton } from "../components/Button";
import { ErrorMessage } from "../components/ErrorMessage";
import { CausesField, PhoneField, PostalCodeField } from "../components/ProfileFields";
import { useAction } from "../hooks/useAction";

export function DonorForm({ onBack }: Readonly<{ onBack: () => void }>) {
  const { setUser } = useAuth();
  const { errorMessage, pending, run } = useAction();
  const [postalCode, setPostalCode] = useState("");
  const [phone, setPhone] = useState("");
  const [preferredCauses, setPreferredCauses] = useState<Cause[]>([]);

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
        <PostalCodeField value={postalCode} onChange={setPostalCode} />
        <PhoneField optional value={phone} onChange={setPhone} />
        <CausesField value={preferredCauses} onChange={setPreferredCauses} />
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
