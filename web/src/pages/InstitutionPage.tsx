import { useEffect, useState, type ReactNode } from "react";
import { useParams } from "react-router";
import {
  getPublicInstitution,
  type InstitutionWithNeeds,
  type OpenNeed,
} from "../api/institutions";
import { causeLabels } from "../causes";
import { ErrorMessage } from "../components/ErrorMessage";
import { Section } from "../components/Section";
import { friendlyMessage } from "../errors";
import { formatAddress, formatPhone } from "../format";
import { institutionTypeLabels, institutionVerdictLabels } from "./institutionLabels";

const LINK_CLASS = "text-sky-800 underline";

interface InstitutionProps {
  institution: InstitutionWithNeeds;
}

function Detail({
  label,
  wide = false,
  children,
}: Readonly<{ label: string; wide?: boolean; children: ReactNode }>) {
  return (
    <div className={wide ? "sm:col-span-2" : undefined}>
      <dt className="text-sm text-slate-600">{label}</dt>
      <dd className="font-semibold wrap-anywhere">{children}</dd>
    </div>
  );
}

function AboutSection({ institution }: Readonly<InstitutionProps>) {
  return (
    <Section title="Sobre a instituição">
      <div className="space-y-4 sm:col-span-2">
        {institution.description && (
          <p className="whitespace-pre-line">{institution.description}</p>
        )}
        {institution.causes.length > 0 && (
          <ul aria-label="Causas atendidas" className="flex flex-wrap gap-2">
            {institution.causes.map((cause) => (
              <li key={cause} className="rounded-full bg-sky-100 px-4 py-2 text-sky-950">
                {causeLabels[cause]}
              </li>
            ))}
          </ul>
        )}
      </div>
    </Section>
  );
}

function NeedsSection({ needs }: Readonly<{ needs: OpenNeed[] }>) {
  return (
    <Section title="Necessidades abertas">
      <div className="sm:col-span-2">
        {needs.length === 0 ? (
          <p className="text-slate-600">Nenhuma necessidade aberta no momento.</p>
        ) : (
          <ul className="space-y-4">
            {needs.map((need) => (
              <li key={need.id}>
                <h3 className="font-bold">{need.title}</h3>
                {need.quantity && <p className="text-slate-600">Quantidade: {need.quantity}</p>}
                <p className="whitespace-pre-line">{need.description}</p>
              </li>
            ))}
          </ul>
        )}
      </div>
    </Section>
  );
}

function ContactsSection({ institution }: Readonly<InstitutionProps>) {
  const links = [
    ["Site", institution.website],
    ["Instagram", institution.instagram],
    ["Facebook", institution.facebook],
  ] as const;

  return (
    <Section title="Contatos e endereço">
      <dl className="grid gap-x-4 gap-y-6 sm:col-span-2 sm:grid-cols-2">
        {institution.phone && (
          <Detail label="Telefone / WhatsApp">{formatPhone(institution.phone)}</Detail>
        )}
        {institution.contact_email && (
          <Detail label="E-mail">
            <a href={`mailto:${institution.contact_email}`} className={LINK_CLASS}>
              {institution.contact_email}
            </a>
          </Detail>
        )}
        {links.map(
          ([label, url]) =>
            url && (
              <Detail key={label} label={label}>
                <a href={url} target="_blank" rel="noreferrer" className={LINK_CLASS}>
                  {url.replace(/^https?:\/\//, "")}
                </a>
              </Detail>
            ),
        )}
        <Detail label="Endereço" wide>
          {formatAddress(institution)}
        </Detail>
      </dl>
    </Section>
  );
}

function InstitutionDetails({ institution }: Readonly<InstitutionProps>) {
  return (
    <section className="rounded border border-slate-200 bg-white p-6 sm:p-8">
      <h1 className="text-4xl font-extrabold wrap-anywhere">
        {institution.trade_name ?? institution.legal_name}
      </h1>
      <div className="my-6 rounded-lg bg-slate-100 p-4">
        <p className="text-xl font-bold">
          {institutionTypeLabels[institution.type]} em {institution.city}, {institution.state}
        </p>
        <p className="text-slate-600">{institutionVerdictLabels[institution.verdict]}</p>
        <p className="text-slate-600 wrap-anywhere">
          {institution.trade_name && `${institution.legal_name}, `}CNPJ {institution.cnpj}
        </p>
      </div>
      <div className="divide-y divide-slate-200 border-t border-slate-200">
        <AboutSection institution={institution} />
        <NeedsSection needs={institution.open_needs} />
        <ContactsSection institution={institution} />
      </div>
    </section>
  );
}

export function InstitutionPage() {
  const { id = "" } = useParams();
  const validId = /^\d+$/.test(id) && Number(id) > 0;
  const [institution, setInstitution] = useState<InstitutionWithNeeds | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    if (!validId) return;
    let active = true;
    getPublicInstitution(Number(id))
      .then((found) => {
        if (active) setInstitution(found);
      })
      .catch((error: unknown) => {
        if (active) setErrorMessage(friendlyMessage(error));
      });
    return () => {
      active = false;
    };
  }, [id, validId]);

  if (!validId) return <ErrorMessage message="Instituição não encontrada." />;
  if (errorMessage) return <ErrorMessage message={errorMessage} />;
  if (!institution) return <output className="block">Carregando instituição…</output>;
  return <InstitutionDetails institution={institution} />;
}
