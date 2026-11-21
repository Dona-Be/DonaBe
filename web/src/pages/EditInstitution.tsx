import { useEffect, useState } from "react";
import { Link, useParams } from "react-router";
import { listMyInstitutions, type Institution } from "../api/institutions";
import { ErrorMessage } from "../components/ErrorMessage";
import { friendlyMessage } from "../errors";
import { routes } from "../routes";
import { InstitutionForm } from "./InstitutionForm";

export function EditInstitution() {
  const { id } = useParams();
  const institutionId = Number(id);
  const [institution, setInstitution] = useState<Institution | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    listMyInstitutions()
      .then((items) => {
        if (!active) return;
        const found = items.find((item) => item.id === institutionId);
        if (found) setInstitution(found);
        else setErrorMessage("Instituição não encontrada entre as suas instituições.");
      })
      .catch((error: unknown) => {
        if (active) setErrorMessage(friendlyMessage(error));
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [institutionId]);

  if (loading) return <p role="status">Carregando instituição…</p>;
  if (errorMessage) {
    return (
      <section className="space-y-4 rounded border border-slate-200 bg-white p-6">
        <ErrorMessage message={errorMessage} />
        <Link to={routes.institutions} className="text-sky-800 underline">
          Voltar para minhas instituições
        </Link>
      </section>
    );
  }
  if (!institution) return null;
  return <InstitutionForm key={institution.id} existing={institution} />;
}
