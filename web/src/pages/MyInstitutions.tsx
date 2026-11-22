import { useEffect, useState } from "react";
import { Link } from "react-router";
import { listMyInstitutions, type Institution } from "../api/institutions";
import { ErrorMessage } from "../components/ErrorMessage";
import { friendlyMessage } from "../errors";
import { routes } from "../routes";
import { institutionTypeLabels, institutionVerdictLabels } from "./institutionLabels";

export function MyInstitutions() {
  const [institutions, setInstitutions] = useState<Institution[]>([]);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    listMyInstitutions()
      .then((items) => {
        if (active) setInstitutions(items);
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
  }, []);

  return (
    <section className="space-y-6 rounded border border-slate-200 bg-white p-6 sm:p-8">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <h1 className="text-3xl font-extrabold sm:text-4xl">Minhas instituições</h1>
        <Link
          to={routes.newInstitution}
          className="inline-flex h-14 items-center justify-center rounded-full bg-sky-300 px-6 font-bold text-sky-950 hover:bg-sky-400 sm:px-8"
        >
          Cadastrar instituição
        </Link>
      </div>

      {errorMessage && <ErrorMessage message={errorMessage} />}
      {loading && <p role="status">Carregando instituições…</p>}
      {!loading && !errorMessage && institutions.length === 0 && (
        <div className="rounded-xl bg-slate-100 p-6">
          <h2 className="text-xl font-bold">Você ainda não cadastrou uma instituição</h2>
          <p className="mt-2 text-slate-600">
            Cadastre pelo CNPJ para que os doadores possam conhecer seu trabalho.
          </p>
        </div>
      )}
      {!loading && institutions.length > 0 && (
        <ul className="space-y-4">
          {institutions.map((institution) => (
            <li key={institution.id} className="rounded-xl border border-slate-200 p-5">
              <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                <div className="space-y-2">
                  <h2 className="text-xl font-bold">
                    {institution.trade_name ?? institution.legal_name}
                  </h2>
                  <p className="text-slate-600">
                    {institutionTypeLabels[institution.type]} ·{" "}
                    {institutionVerdictLabels[institution.verdict]}
                  </p>
                  <p className="text-slate-600">
                    {institution.city}, {institution.state} · CNPJ {institution.cnpj}
                  </p>
                  {institution.description && <p>{institution.description}</p>}
                </div>
                <Link
                  to={`${routes.institutions}/${String(institution.id)}/editar`}
                  className="shrink-0 rounded-full border border-slate-500 px-5 py-3 text-center font-bold hover:bg-slate-50"
                >
                  Editar
                </Link>
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
