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
import { PrimaryButton, SECONDARY_CLASS, SecondaryButton } from "../components/Button";
import { ErrorMessage } from "../components/ErrorMessage";
import { CausesField, PhoneField } from "../components/ProfileFields";
import { Section } from "../components/Section";
import { TextField } from "../components/TextField";
import { formatPostalCode, joinPhone, splitPhone, type Phone } from "../format";
import { useAction } from "../hooks/useAction";
import { routes } from "../routes";
import { institutionTypeLabels, institutionVerdictLabels } from "./institutionLabels";

type InstitutionFormValues = Omit<InstitutionChanges, "phone"> & { phone: Phone };
type ValueChange = <Field extends keyof InstitutionFormValues>(
  field: Field,
  value: InstitutionFormValues[Field],
) => void;

const EMAIL_PATTERN = String.raw`[^@\s]+@[^@\s]+\.[^@\s]+`;
const LINK_PATTERN = String.raw`https?://\S+`;
const LINK_TITLE = "Comece com http:// ou https://";

function emptyFormValues(): InstitutionFormValues {
  return {
    trade_name: "",
    description: "",
    causes: [],
    phone: splitPhone(""),
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
    postal_code: formatPostalCode(stringValue(institution.postal_code)),
  };
  if (!("id" in institution)) return officialValues;

  return {
    ...officialValues,
    description: stringValue(institution.description),
    causes: institution.causes,
    phone: splitPhone(stringValue(institution.phone)),
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
    formatPostalCode(stringValue(institution.postal_code)),
  ]
    .filter(Boolean)
    .join(", ");

  return (
    <section
      aria-label="Dados oficiais do CNPJ"
      className="my-6 space-y-4 rounded-lg bg-slate-100 p-4"
    >
      <h2 className="text-xl font-bold">Dados oficiais do CNPJ</h2>
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
          <dt className="text-sm text-slate-600">Endereço</dt>
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
  errorMessage: string | null;
  onCnpjChange: (value: string) => void;
  onLookup: (event: SubmitEvent<HTMLFormElement>) => void;
  onContinue: () => void;
}

function LookupStep({
  cnpj,
  preview,
  pending,
  errorMessage,
  onCnpjChange,
  onLookup,
  onContinue,
}: Readonly<LookupStepProps>) {
  return (
    <>
      <form onSubmit={onLookup} className="mt-6 space-y-4">
        <TextField
          label="CNPJ"
          hint="Digite os 14 números do CNPJ."
          inputMode="numeric"
          autoComplete="off"
          maxLength={18}
          readOnly={pending}
          value={cnpj}
          onChange={(event) => onCnpjChange(event.target.value)}
        />
        {errorMessage && <ErrorMessage message={errorMessage} />}
        <div className="flex justify-end">
          <PrimaryButton disabled={pending}>Consultar CNPJ</PrimaryButton>
        </div>
      </form>
      {preview && (
        <>
          <InstitutionSummary institution={preview} />
          <div className="flex justify-end">
            <PrimaryButton disabled={pending} onClick={onContinue}>
              Continuar para os detalhes
            </PrimaryButton>
          </div>
        </>
      )}
    </>
  );
}

interface DetailsStepProps {
  preview: InstitutionPreview;
  values: InstitutionFormValues;
  isEditing: boolean;
  pending: boolean;
  errorMessage: string | null;
  onSave: (event: SubmitEvent<HTMLFormElement>) => void;
  onBack: () => void;
  onValueChange: ValueChange;
}

function DetailsStep({
  preview,
  values,
  isEditing,
  pending,
  errorMessage,
  onSave,
  onBack,
  onValueChange,
}: Readonly<DetailsStepProps>) {
  return (
    <>
      <InstitutionSummary institution={preview} />
      <form onSubmit={onSave} className="divide-y divide-slate-200 border-t border-slate-200">
        <Section title="Sobre a instituição">
          <div className="sm:col-span-2">
            <TextField
              label="Nome fantasia"
              maxLength={200}
              value={values.trade_name}
              onChange={(event) => onValueChange("trade_name", event.target.value)}
            />
          </div>
          <div className="sm:col-span-2">
            <label htmlFor="institution-description" className="mb-2 block font-bold">
              Descrição
            </label>
            <textarea
              id="institution-description"
              aria-describedby="institution-description-hint"
              required
              maxLength={2000}
              rows={5}
              value={values.description}
              onChange={(event) => onValueChange("description", event.target.value)}
              className="w-full rounded-lg border border-slate-500 p-4 focus:border-sky-700 focus:outline-1 focus:outline-sky-700"
            />
            <p id="institution-description-hint" className="mt-2 text-slate-600">
              Conte um pouco sobre o trabalho realizado.
            </p>
          </div>
          <div className="sm:col-span-2">
            <CausesField
              legend="Causas atendidas"
              value={values.causes}
              onChange={(causes) => onValueChange("causes", causes)}
            />
          </div>
        </Section>
        <Section title="Contatos">
          <PhoneField value={values.phone} onChange={(phone) => onValueChange("phone", phone)} />
          <TextField
            label="E-mail de contato"
            optional
            type="email"
            maxLength={200}
            pattern={EMAIL_PATTERN}
            title="Um e-mail como nome@exemplo.org"
            autoComplete="email"
            value={values.contact_email}
            onChange={(event) => onValueChange("contact_email", event.target.value)}
          />
          <TextField
            label="Site"
            optional
            type="url"
            pattern={LINK_PATTERN}
            title={LINK_TITLE}
            placeholder="https://"
            value={values.website}
            onChange={(event) => onValueChange("website", event.target.value)}
          />
          <TextField
            label="Instagram"
            optional
            type="url"
            pattern={LINK_PATTERN}
            title={LINK_TITLE}
            placeholder="https://instagram.com/"
            value={values.instagram}
            onChange={(event) => onValueChange("instagram", event.target.value)}
          />
          <TextField
            label="Facebook"
            optional
            type="url"
            pattern={LINK_PATTERN}
            title={LINK_TITLE}
            placeholder="https://facebook.com/"
            value={values.facebook}
            onChange={(event) => onValueChange("facebook", event.target.value)}
          />
        </Section>
        <Section title="Endereço">
          <div className="sm:col-span-2">
            <TextField
              label="Rua"
              value={values.street}
              onChange={(event) => onValueChange("street", event.target.value)}
            />
          </div>
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
          <TextField
            label="Bairro"
            value={values.neighborhood}
            onChange={(event) => onValueChange("neighborhood", event.target.value)}
          />
          <div className="grid grid-cols-[1fr_5rem] gap-3">
            <TextField
              label="Cidade"
              value={values.city}
              onChange={(event) => onValueChange("city", event.target.value)}
            />
            <TextField
              label="UF"
              maxLength={2}
              pattern="[A-Za-z]{2}"
              title="Duas letras"
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
        </Section>
        <div className="space-y-4 pt-6">
          {errorMessage && <ErrorMessage message={errorMessage} />}
          <div className="flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
            {isEditing ? (
              <Link
                to={routes.institutions}
                className={`${SECONDARY_CLASS} flex items-center justify-center`}
              >
                Cancelar
              </Link>
            ) : (
              <SecondaryButton disabled={pending} onClick={onBack}>
                Voltar
              </SecondaryButton>
            )}
            <PrimaryButton disabled={pending}>
              {isEditing ? "Salvar alterações" : "Cadastrar instituição"}
            </PrimaryButton>
          </div>
        </div>
      </form>
    </>
  );
}

function titleFor(isEditing: boolean, step: "lookup" | "details"): string {
  if (isEditing) return "Editar instituição";
  if (step === "lookup") return "Consulte o CNPJ";
  return "Complete os dados";
}

function initialStep(existing: Institution | undefined): "lookup" | "details" {
  return existing === undefined ? "lookup" : "details";
}

interface FormBodyProps {
  step: "lookup" | "details";
  cnpj: string;
  preview: InstitutionPreview | null;
  values: InstitutionFormValues;
  isEditing: boolean;
  pending: boolean;
  errorMessage: string | null;
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
  errorMessage,
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
        errorMessage={errorMessage}
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
      errorMessage={errorMessage}
      onSave={onSave}
      onBack={onBack}
      onValueChange={onValueChange}
    />
  );
}

export function InstitutionForm({ existing }: Readonly<{ existing?: Institution }>) {
  const navigate = useNavigate();
  const { errorMessage, setErrorMessage, pending, run } = useAction();
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
      phone: joinPhone(values.phone) ?? "",
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

  function goToStep(next: "lookup" | "details") {
    setErrorMessage(null);
    setStep(next);
  }

  return (
    <section className="rounded border border-slate-200 bg-white p-6 sm:p-8">
      <h1 className="text-4xl font-extrabold">{titleFor(isEditing, step)}</h1>
      <InstitutionFormBody
        step={step}
        cnpj={cnpj}
        preview={preview}
        values={values}
        isEditing={isEditing}
        pending={pending}
        errorMessage={errorMessage}
        onCnpjChange={changeCnpj}
        onLookup={handleLookup}
        onContinue={() => goToStep("details")}
        onSave={handleSave}
        onBack={() => goToStep("lookup")}
        onValueChange={updateValue}
      />
    </section>
  );
}
