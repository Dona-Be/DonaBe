import { useState, type SubmitEvent } from "react";
import { Link, useNavigate } from "react-router";
import {
  createInstitution,
  lookupInstitution,
  updateInstitution,
  type Institution,
  type InstitutionChanges,
  type InstitutionPreview,
} from "../api/institutions";
import { PrimaryButton, SecondaryButton } from "../components/Button";
import { ErrorMessage } from "../components/ErrorMessage";
import { CausesField } from "../components/ProfileFields";
import { TextField } from "../components/TextField";
import { formatPostalCode } from "../format";
import { useAction } from "../hooks/useAction";
import { routes } from "../routes";
import { institutionTypeLabels, institutionVerdictLabels } from "./institutionLabels";

type InstitutionFormValues = InstitutionChanges;
type ValueChange = <Field extends keyof InstitutionFormValues>(
  field: Field,
  value: InstitutionFormValues[Field],
) => void;

function emptyFormValues(): InstitutionFormValues {
  return {
    trade_name: "",
    description: "",
    causes: [],
    phone: "",
    contact_email: "",
    website: "",
    instagram: "",
    facebook: "",
    street: "",
    number: "",
    complement: "",
    neighborhood: "",
    city: "",
    state: "",
    postal_code: "",
  };
}

function stringValue(value: string | null | undefined): string {
  return value ?? "";
}

function initialValues(
  institution: InstitutionPreview | Institution | null,
): InstitutionFormValues {
  const values = emptyFormValues();
  if (!institution) return values;

  const officialValues = {
    ...values,
    trade_name: stringValue(institution.trade_name),
    street: stringValue(institution.street),
    number: stringValue(institution.number),
    complement: stringValue(institution.complement),
    neighborhood: stringValue(institution.neighborhood),
    city: institution.city,
    state: institution.state,
    postal_code: stringValue(institution.postal_code),
  };
  if (!("id" in institution)) return officialValues;

  return {
    ...officialValues,
    description: stringValue(institution.description),
    causes: institution.causes,
    phone: stringValue(institution.phone),
    contact_email: stringValue(institution.contact_email),
    website: stringValue(institution.website),
    instagram: stringValue(institution.instagram),
    facebook: stringValue(institution.facebook),
  };
}

function InstitutionSummary({ institution }: Readonly<{ institution: InstitutionPreview }>) {
  const address = [
    institution.street,
    institution.number,
    institution.complement,
    institution.neighborhood,
    institution.city,
    institution.state,
    institution.postal_code,
  ]
    .filter(Boolean)
    .join(", ");

  return (
    <section aria-label="Dados oficiais do CNPJ" className="space-y-4 rounded-xl bg-slate-100 p-5">
      <div>
        <h2 className="text-xl font-bold">Dados oficiais do CNPJ</h2>
        <p className="text-slate-600">Confira as informações consultadas antes de continuar.</p>
      </div>
      <dl className="grid gap-x-6 gap-y-3 sm:grid-cols-2">
        <div>
          <dt className="text-sm text-slate-600">Razão social</dt>
          <dd className="font-semibold">{institution.legal_name}</dd>
        </div>
        <div>
          <dt className="text-sm text-slate-600">CNPJ</dt>
          <dd className="font-semibold">{institution.cnpj}</dd>
        </div>
        <div>
          <dt className="text-sm text-slate-600">Tipo</dt>
          <dd className="font-semibold">{institutionTypeLabels[institution.type]}</dd>
        </div>
        <div>
          <dt className="text-sm text-slate-600">Veredito</dt>
          <dd className="font-semibold">{institutionVerdictLabels[institution.verdict]}</dd>
        </div>
        <div className="sm:col-span-2">
          <dt className="text-sm text-slate-600">Endereço oficial</dt>
          <dd className="font-semibold">{address || "Endereço não informado"}</dd>
        </div>
      </dl>
      <div>
        <h3 className="font-bold">Motivos da classificação</h3>
        <ul className="mt-2 list-inside list-disc space-y-1 text-slate-700">
          {institution.reasons.map((reason) => (
            <li key={reason}>{reason}</li>
          ))}
        </ul>
      </div>
    </section>
  );
}

interface LookupStepProps {
  cnpj: string;
  preview: InstitutionPreview | null;
  pending: boolean;
  onCnpjChange: (value: string) => void;
  onLookup: (event: SubmitEvent<HTMLFormElement>) => void;
  onContinue: () => void;
}

function LookupStep({
  cnpj,
  preview,
  pending,
  onCnpjChange,
  onLookup,
  onContinue,
}: Readonly<LookupStepProps>) {
  return (
    <div className="space-y-6">
      <form onSubmit={onLookup} className="space-y-5">
        <TextField
          label="CNPJ"
          hint="Digite os 14 números do CNPJ."
          inputMode="numeric"
          autoComplete="off"
          maxLength={18}
          value={cnpj}
          onChange={(event) => onCnpjChange(event.target.value)}
        />
        <PrimaryButton disabled={pending} className="w-full sm:w-auto">
          Consultar CNPJ
        </PrimaryButton>
      </form>
      {preview && (
        <>
          <InstitutionSummary institution={preview} />
          <PrimaryButton disabled={pending} className="w-full sm:w-auto" onClick={onContinue}>
            Continuar para os detalhes
          </PrimaryButton>
        </>
      )}
    </div>
  );
}

interface DetailsStepProps {
  preview: InstitutionPreview;
  values: InstitutionFormValues;
  isEditing: boolean;
  pending: boolean;
  onSave: (event: SubmitEvent<HTMLFormElement>) => void;
  onBack: () => void;
  onValueChange: ValueChange;
}

function DetailsStep({
  preview,
  values,
  isEditing,
  pending,
  onSave,
  onBack,
  onValueChange,
}: Readonly<DetailsStepProps>) {
  return (
    <form onSubmit={onSave} className="space-y-6">
      <InstitutionSummary institution={preview} />
      <fieldset className="space-y-5">
        <legend className="text-xl font-bold">Sobre a instituição</legend>
        <TextField
          label="Nome fantasia"
          maxLength={200}
          value={values.trade_name}
          onChange={(event) => onValueChange("trade_name", event.target.value)}
        />
        <div>
          <label htmlFor="institution-description" className="mb-2 block font-bold">
            Descrição
          </label>
          <textarea
            id="institution-description"
            required
            maxLength={2000}
            rows={5}
            value={values.description}
            onChange={(event) => onValueChange("description", event.target.value)}
            className="w-full rounded-lg border border-slate-500 p-4 focus:border-sky-700 focus:outline-1 focus:outline-sky-700"
          />
          <p className="mt-2 text-sm text-slate-600">Conte um pouco sobre o trabalho realizado.</p>
        </div>
        <CausesField
          legend="Causas atendidas"
          value={values.causes}
          onChange={(causes) => onValueChange("causes", causes)}
        />
      </fieldset>

      <fieldset className="space-y-5">
        <legend className="text-xl font-bold">Contatos</legend>
        <TextField
          label="Telefone / WhatsApp"
          optional
          type="tel"
          autoComplete="tel"
          value={values.phone}
          onChange={(event) => onValueChange("phone", event.target.value)}
        />
        <TextField
          label="E-mail de contato"
          optional
          type="email"
          autoComplete="email"
          value={values.contact_email}
          onChange={(event) => onValueChange("contact_email", event.target.value)}
        />
        <TextField
          label="Site"
          optional
          type="url"
          placeholder="https://"
          value={values.website}
          onChange={(event) => onValueChange("website", event.target.value)}
        />
        <TextField
          label="Instagram"
          optional
          type="url"
          placeholder="https://instagram.com/"
          value={values.instagram}
          onChange={(event) => onValueChange("instagram", event.target.value)}
        />
        <TextField
          label="Facebook"
          optional
          type="url"
          placeholder="https://facebook.com/"
          value={values.facebook}
          onChange={(event) => onValueChange("facebook", event.target.value)}
        />
      </fieldset>

      <fieldset className="space-y-5">
        <legend className="text-xl font-bold">Endereço</legend>
        <p className="-mt-3 text-slate-600">Você pode corrigir ou completar o endereço oficial.</p>
        <TextField
          label="Rua"
          value={values.street}
          onChange={(event) => onValueChange("street", event.target.value)}
        />
        <div className="grid gap-5 sm:grid-cols-2">
          <TextField
            label="Número"
            value={values.number}
            onChange={(event) => onValueChange("number", event.target.value)}
          />
          <TextField
            label="Complemento"
            optional
            value={values.complement}
            onChange={(event) => onValueChange("complement", event.target.value)}
          />
        </div>
        <TextField
          label="Bairro"
          value={values.neighborhood}
          onChange={(event) => onValueChange("neighborhood", event.target.value)}
        />
        <div className="grid gap-5 sm:grid-cols-[1fr_6rem]">
          <TextField
            label="Cidade"
            value={values.city}
            onChange={(event) => onValueChange("city", event.target.value)}
          />
          <TextField
            label="UF"
            maxLength={2}
            value={values.state}
            onChange={(event) => onValueChange("state", event.target.value.toUpperCase())}
          />
        </div>
        <TextField
          label="CEP"
          inputMode="numeric"
          autoComplete="postal-code"
          value={values.postal_code}
          onChange={(event) => onValueChange("postal_code", event.target.value)}
          onBlur={() => onValueChange("postal_code", formatPostalCode(values.postal_code))}
        />
      </fieldset>

      <div className="flex flex-col gap-3 sm:flex-row">
        {!isEditing && (
          <SecondaryButton disabled={pending} onClick={onBack}>
            Voltar
          </SecondaryButton>
        )}
        <PrimaryButton disabled={pending} className="flex-1">
          {isEditing ? "Salvar alterações" : "Cadastrar instituição"}
        </PrimaryButton>
      </div>
    </form>
  );
}

function titleFor(isEditing: boolean, step: "lookup" | "details"): string {
  if (isEditing) return "Editar instituição";
  if (step === "lookup") return "Consulte o CNPJ";
  return "Complete os dados";
}

function descriptionFor(isEditing: boolean, step: "lookup" | "details"): string {
  if (isEditing) return "Atualize os dados de contato, causas e endereço da instituição.";
  if (step === "lookup") {
    return "Informe o CNPJ para conferir os dados oficiais e a classificação da instituição.";
  }
  return "Confira os dados oficiais e complete as informações que os doadores verão.";
}

function initialStep(existing: Institution | undefined): "lookup" | "details" {
  return existing === undefined ? "lookup" : "details";
}

function InstitutionFormHeader({
  isEditing,
  step,
}: Readonly<{ isEditing: boolean; step: "lookup" | "details" }>) {
  const eyebrow = isEditing ? "Minhas instituições" : "Cadastro de instituição";
  return (
    <div>
      <p className="font-semibold text-sky-800">{eyebrow}</p>
      <h1 className="mt-2 text-3xl font-extrabold sm:text-4xl">{titleFor(isEditing, step)}</h1>
      <p className="mt-2 text-slate-600">{descriptionFor(isEditing, step)}</p>
    </div>
  );
}

interface FormBodyProps {
  step: "lookup" | "details";
  cnpj: string;
  preview: InstitutionPreview | null;
  values: InstitutionFormValues;
  isEditing: boolean;
  pending: boolean;
  onCnpjChange: (value: string) => void;
  onLookup: (event: SubmitEvent<HTMLFormElement>) => void;
  onContinue: () => void;
  onSave: (event: SubmitEvent<HTMLFormElement>) => void;
  onBack: () => void;
  onValueChange: ValueChange;
}

function InstitutionFormBody({
  step,
  cnpj,
  preview,
  values,
  isEditing,
  pending,
  onCnpjChange,
  onLookup,
  onContinue,
  onSave,
  onBack,
  onValueChange,
}: Readonly<FormBodyProps>) {
  if (step === "lookup") {
    return (
      <LookupStep
        cnpj={cnpj}
        preview={preview}
        pending={pending}
        onCnpjChange={onCnpjChange}
        onLookup={onLookup}
        onContinue={onContinue}
      />
    );
  }
  if (!preview) return null;
  return (
    <DetailsStep
      preview={preview}
      values={values}
      isEditing={isEditing}
      pending={pending}
      onSave={onSave}
      onBack={onBack}
      onValueChange={onValueChange}
    />
  );
}

export function InstitutionForm({ existing }: Readonly<{ existing?: Institution }>) {
  const navigate = useNavigate();
  const { errorMessage, pending, run } = useAction();
  const [cnpj, setCnpj] = useState(existing?.cnpj ?? "");
  const [preview, setPreview] = useState<InstitutionPreview | null>(existing ?? null);
  const [step, setStep] = useState<"lookup" | "details">(initialStep(existing));
  const [values, setValues] = useState<InstitutionFormValues>(() =>
    initialValues(existing ?? null),
  );
  const isEditing = existing !== undefined;

  function handleLookup(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault();
    run(async () => {
      const result = await lookupInstitution(cnpj.trim());
      setPreview(result);
      setValues(initialValues(result));
    });
  }

  const updateValue: ValueChange = (field, value) => {
    setValues((current) => ({ ...current, [field]: value }));
  };

  function handleSave(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!preview) return;
    const changes = {
      ...values,
      postal_code: formatPostalCode(values.postal_code),
    } satisfies InstitutionChanges;

    run(async () => {
      if (existing) await updateInstitution(existing.id, changes);
      else await createInstitution({ cnpj: preview.cnpj, ...changes });
      void navigate(routes.institutions);
    });
  }

  function changeCnpj(value: string) {
    setCnpj(value);
    setPreview(null);
  }

  return (
    <section className="space-y-6 rounded border border-slate-200 bg-white p-6 sm:p-8">
      <InstitutionFormHeader isEditing={isEditing} step={step} />
      {errorMessage && <ErrorMessage message={errorMessage} />}
      <InstitutionFormBody
        step={step}
        cnpj={cnpj}
        preview={preview}
        values={values}
        isEditing={isEditing}
        pending={pending}
        onCnpjChange={changeCnpj}
        onLookup={handleLookup}
        onContinue={() => setStep("details")}
        onSave={handleSave}
        onBack={() => setStep("lookup")}
        onValueChange={updateValue}
      />

      <Link to={routes.institutions} className="inline-block text-sky-800 underline">
        Minhas instituições
      </Link>
    </section>
  );
}
