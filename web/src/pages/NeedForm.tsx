import { useId, useState, type SubmitEvent } from "react";
import type { Need, NeedChanges } from "../api/needs";
import { PrimaryButton, SecondaryButton } from "../components/Button";
import { ErrorMessage } from "../components/ErrorMessage";
import { TextField } from "../components/TextField";
import { useAction } from "../hooks/useAction";

interface NeedFormProps {
  existing?: Need;
  onSave: (changes: NeedChanges) => Promise<void>;
  onCancel: () => void;
}

const TEXTAREA_CLASS =
  "w-full rounded-lg border border-slate-500 p-4 focus:border-sky-700 focus:outline-1 " +
  "focus:outline-sky-700";

function initialValues(need: Need | undefined): NeedChanges {
  return {
    title: need?.title ?? "",
    description: need?.description ?? "",
    quantity: need?.quantity ?? "",
  };
}

export function NeedForm({ existing, onSave, onCancel }: Readonly<NeedFormProps>) {
  const id = useId();
  const { errorMessage, pending, run } = useAction();
  const [values, setValues] = useState<NeedChanges>(() => initialValues(existing));
  const isEditing = existing !== undefined;
  const heading = isEditing ? "Editar necessidade" : "Nova necessidade";

  function update(field: keyof NeedChanges, value: string) {
    setValues((current) => ({ ...current, [field]: value }));
  }

  function handleSubmit(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault();
    run(() =>
      onSave({
        title: values.title.trim(),
        description: values.description.trim(),
        quantity: values.quantity.trim(),
      }),
    );
  }

  return (
    <form
      aria-label={heading}
      onSubmit={handleSubmit}
      className="space-y-5 rounded-xl border-2 border-sky-200 p-5"
    >
      <h2 className="text-xl font-bold">{heading}</h2>
      <TextField
        label="Título"
        hint="O que a instituição precisa, como “Cobertores de casal”."
        maxLength={200}
        value={values.title}
        onChange={(event) => update("title", event.target.value)}
      />
      <div>
        <label htmlFor={`${id}-description`} className="mb-2 block font-bold">
          Descrição
        </label>
        <textarea
          id={`${id}-description`}
          aria-describedby={`${id}-description-hint`}
          required
          maxLength={2000}
          rows={4}
          value={values.description}
          onChange={(event) => update("description", event.target.value)}
          className={TEXTAREA_CLASS}
        />
        <p id={`${id}-description-hint`} className="mt-2 text-slate-600">
          Conte para que serve e como os doadores podem ajudar.
        </p>
      </div>
      <TextField
        label="Quantidade"
        optional
        hint="Como “20 unidades” ou “10 kg”."
        maxLength={200}
        value={values.quantity}
        onChange={(event) => update("quantity", event.target.value)}
      />
      {errorMessage && <ErrorMessage message={errorMessage} />}
      <div className="flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
        <SecondaryButton disabled={pending} onClick={onCancel}>
          Cancelar
        </SecondaryButton>
        <PrimaryButton disabled={pending}>
          {isEditing ? "Salvar alterações" : "Publicar necessidade"}
        </PrimaryButton>
      </div>
    </form>
  );
}
