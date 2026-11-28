import { useEffect, useState, type Dispatch, type SetStateAction } from "react";
import { Link, useParams } from "react-router";
import { listMyInstitutions, type Institution } from "../api/institutions";
import {
  closeNeed,
  createNeed,
  fulfillNeed,
  listInstitutionNeeds,
  updateNeed,
  type Need,
  type NeedChanges,
  type NeedStatus,
} from "../api/needs";
import { PRIMARY_CLASS } from "../components/Button";
import { ConfirmDialog } from "../components/ConfirmDialog";
import { ErrorMessage } from "../components/ErrorMessage";
import { FriendlyError, friendlyMessage } from "../errors";
import { formatDate } from "../format";
import { useAction } from "../hooks/useAction";
import { routes } from "../routes";
import { NeedForm } from "./NeedForm";

type StatusChange = "fulfill" | "close";

interface PendingChange {
  need: Need;
  change: StatusChange;
}

const STATUSES: NeedStatus[] = ["open", "fulfilled", "closed"];

const filterLabels: Record<NeedStatus, string> = {
  open: "Abertas",
  fulfilled: "Atendidas",
  closed: "Encerradas",
};

const statusLabels: Record<NeedStatus, string> = {
  open: "Aberta",
  fulfilled: "Atendida",
  closed: "Encerrada",
};

const emptyFilterMessages: Record<NeedStatus, string> = {
  open: "Nenhuma necessidade aberta. Os doadores não veem pedidos desta instituição no momento.",
  fulfilled: "Nenhuma necessidade marcada como atendida ainda.",
  closed: "Nenhuma necessidade encerrada.",
};

const badgeClasses: Record<NeedStatus, string> = {
  open: "bg-sky-100 text-sky-950",
  fulfilled: "bg-emerald-100 text-emerald-900",
  closed: "bg-slate-200 text-slate-700",
};

const NOT_MINE = "Instituição não encontrada entre as suas instituições.";
const UNAVAILABLE_TO_DONORS = "deixa de aparecer para os doadores e não recebe novos interesses.";

const changeTexts: Record<
  StatusChange,
  { title: string; confirm: string; message: (title: string) => string; done: string }
> = {
  fulfill: {
    title: "Marcar como atendida?",
    confirm: "Marcar como atendida",
    message: (title) =>
      `Use quando a instituição já recebeu o suficiente. “${title}” ${UNAVAILABLE_TO_DONORS}`,
    done: "foi marcada como atendida.",
  },
  close: {
    title: "Encerrar necessidade?",
    confirm: "Encerrar",
    message: (title) =>
      `Use quando ela não for mais necessária. “${title}” ${UNAVAILABLE_TO_DONORS}`,
    done: "foi encerrada.",
  },
};

const ACTION_CLASS =
  "rounded-full border border-slate-500 px-5 py-3 font-bold hover:bg-slate-50 " +
  "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-sky-700";
const FULFILL_CLASS =
  "rounded-full border border-emerald-700 px-5 py-3 font-bold text-emerald-900 " +
  "hover:bg-emerald-50 focus-visible:outline-2 focus-visible:outline-offset-2 " +
  "focus-visible:outline-sky-700";
const FILTER_CLASS =
  "cursor-pointer rounded-full border border-slate-500 px-4 py-2 aria-pressed:border-sky-700 " +
  "aria-pressed:bg-sky-100 aria-pressed:ring-1 aria-pressed:ring-sky-700 " +
  "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-sky-700";

function useManagedNeeds(institutionId: number) {
  const [institution, setInstitution] = useState<Institution | null>(null);
  const [needs, setNeeds] = useState<Need[]>([]);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    async function load() {
      const found = (await listMyInstitutions()).find((item) => item.id === institutionId);
      if (!found) throw new FriendlyError(NOT_MINE);
      const items = await listInstitutionNeeds(found.id);
      if (!active) return;
      setInstitution(found);
      setNeeds(items);
    }
    load()
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

  return { institution, needs, setNeeds, errorMessage, loading };
}

function StatusFilter({
  needs,
  value,
  onChange,
}: Readonly<{ needs: Need[]; value: NeedStatus; onChange: (status: NeedStatus) => void }>) {
  return (
    <fieldset aria-label="Filtrar por status" className="flex flex-wrap gap-2">
      {STATUSES.map((status) => (
        <button
          key={status}
          type="button"
          aria-pressed={status === value}
          onClick={() => onChange(status)}
          className={FILTER_CLASS}
        >
          {filterLabels[status]}{" "}
          <span className="font-bold">{needs.filter((need) => need.status === status).length}</span>
        </button>
      ))}
    </fieldset>
  );
}

interface NeedCardProps {
  need: Need;
  onEdit: () => void;
  onChangeStatus: (change: StatusChange) => void;
}

function NeedCard({ need, onEdit, onChangeStatus }: Readonly<NeedCardProps>) {
  const isOpen = need.status === "open";

  return (
    <article aria-label={need.title} className="space-y-3 rounded-xl border border-slate-200 p-5">
      <div className="flex flex-wrap items-center gap-3">
        <h3 className="text-xl font-bold wrap-anywhere">{need.title}</h3>
        <span
          className={`rounded-full px-3 py-1 text-sm font-semibold ${badgeClasses[need.status]}`}
        >
          {statusLabels[need.status]}
        </span>
      </div>
      {need.quantity && <p className="text-slate-600">Quantidade: {need.quantity}</p>}
      <p className="whitespace-pre-line wrap-anywhere">{need.description}</p>
      {need.closed_at && (
        <p className="text-sm text-slate-600">
          {statusLabels[need.status]} em {formatDate(need.closed_at)}
        </p>
      )}
      {isOpen && (
        <div className="flex flex-wrap gap-3 pt-2">
          <button type="button" onClick={onEdit} className={ACTION_CLASS}>
            Editar
          </button>
          <button type="button" onClick={() => onChangeStatus("fulfill")} className={FULFILL_CLASS}>
            Marcar como atendida
          </button>
          <button type="button" onClick={() => onChangeStatus("close")} className={ACTION_CLASS}>
            Encerrar
          </button>
        </div>
      )}
    </article>
  );
}

function EmptyState() {
  return (
    <div className="space-y-4 rounded-xl bg-slate-100 p-6">
      <h2 className="text-xl font-bold">Nenhuma necessidade publicada ainda</h2>
      <p className="text-slate-600">
        Conte aos doadores quais itens a instituição precisa receber: use o botão “Nova
        necessidade”. Cada necessidade aberta aparece na página pública da instituição.
      </p>
    </div>
  );
}

interface NeedListProps {
  needs: Need[];
  statusFilter: NeedStatus;
  editingId: number | null;
  onEdit: (need: Need) => void;
  onSave: (need: Need, changes: NeedChanges) => Promise<void>;
  onCancelEdit: () => void;
  onChangeStatus: (change: PendingChange) => void;
}

function NeedList({
  needs,
  statusFilter,
  editingId,
  onEdit,
  onSave,
  onCancelEdit,
  onChangeStatus,
}: Readonly<NeedListProps>) {
  const shown = needs.filter((need) => need.status === statusFilter);
  if (shown.length === 0)
    return <p className="text-slate-600">{emptyFilterMessages[statusFilter]}</p>;

  return (
    <ul
      aria-label={`Necessidades ${filterLabels[statusFilter].toLowerCase()}`}
      className="space-y-4"
    >
      {shown.map((need) => (
        <li key={need.id}>
          {need.id === editingId ? (
            <NeedForm
              existing={need}
              onSave={(changes) => onSave(need, changes)}
              onCancel={onCancelEdit}
            />
          ) : (
            <NeedCard
              need={need}
              onEdit={() => onEdit(need)}
              onChangeStatus={(change) => onChangeStatus({ need, change })}
            />
          )}
        </li>
      ))}
    </ul>
  );
}

function StatusChangeDialog({
  pendingChange,
  onDone,
  onCancel,
}: Readonly<{
  pendingChange: PendingChange;
  onDone: (need: Need) => void;
  onCancel: () => void;
}>) {
  const { errorMessage, pending, run } = useAction();
  const { need, change } = pendingChange;
  const texts = changeTexts[change];

  function confirm() {
    run(async () => {
      const updated = await (change === "fulfill" ? fulfillNeed(need.id) : closeNeed(need.id));
      onDone(updated);
    });
  }

  return (
    <ConfirmDialog
      title={texts.title}
      message={texts.message(need.title)}
      confirmLabel={texts.confirm}
      pending={pending}
      errorMessage={errorMessage}
      onConfirm={confirm}
      onCancel={onCancel}
    />
  );
}

function NeedsHeader({
  institution,
  onCreate,
}: Readonly<{ institution: Institution; onCreate: () => void }>) {
  return (
    <div className="space-y-4">
      <Link to={routes.institutions} className="text-sky-800 underline">
        Voltar para minhas instituições
      </Link>
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div className="space-y-2">
          <h1 className="text-3xl font-extrabold wrap-anywhere sm:text-4xl">
            Necessidades – {institution.trade_name ?? institution.legal_name}
          </h1>
          <p className="text-slate-600">
            {institution.city}, {institution.state} ·{" "}
            <Link
              to={`${routes.institutions}/${String(institution.id)}`}
              className="text-sky-800 underline"
            >
              Ver página pública
            </Link>
          </p>
        </div>
        <button type="button" onClick={onCreate} className={PRIMARY_CLASS}>
          Nova necessidade
        </button>
      </div>
      <p className="text-slate-600">
        Os doadores veem apenas as necessidades abertas. Marque como atendida quando a instituição
        já tiver recebido o suficiente, ou encerre quando o item não for mais necessário.
      </p>
    </div>
  );
}

function NotFound({ message }: Readonly<{ message: string }>) {
  return (
    <section className="space-y-4 rounded border border-slate-200 bg-white p-6">
      <ErrorMessage message={message} />
      <Link to={routes.institutions} className="text-sky-800 underline">
        Voltar para minhas instituições
      </Link>
    </section>
  );
}

function Notice({ message }: Readonly<{ message: string | null }>) {
  if (!message) return null;
  return (
    <output className="block rounded-lg border border-emerald-200 bg-emerald-50 p-4">
      {message}
    </output>
  );
}

function NeedsManager({
  institution,
  needs,
  setNeeds,
}: Readonly<{
  institution: Institution;
  needs: Need[];
  setNeeds: Dispatch<SetStateAction<Need[]>>;
}>) {
  const [statusFilter, setStatusFilter] = useState<NeedStatus>("open");
  const [creating, setCreating] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [pendingChange, setPendingChange] = useState<PendingChange | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  function replace(updated: Need) {
    setNeeds((current) => current.map((need) => (need.id === updated.id ? updated : need)));
  }

  function startCreating() {
    setEditingId(null);
    setNotice(null);
    setCreating(true);
  }

  async function create(data: NeedChanges) {
    const created = await createNeed(institution.id, data);
    setNeeds((current) => [...current, created]);
    setStatusFilter("open");
    setCreating(false);
    setNotice(`“${created.title}” foi publicada.`);
  }

  async function save(need: Need, data: NeedChanges) {
    replace(await updateNeed(need.id, data));
    setEditingId(null);
    setNotice("Alterações salvas.");
  }

  function finishStatusChange(updated: Need) {
    if (!pendingChange) return;
    replace(updated);
    setNotice(`“${updated.title}” ${changeTexts[pendingChange.change].done}`);
    setPendingChange(null);
  }

  const hasNeeds = needs.length > 0;

  return (
    <section className="space-y-6 rounded border border-slate-200 bg-white p-6 sm:p-8">
      <NeedsHeader institution={institution} onCreate={startCreating} />
      <Notice message={notice} />
      {creating && <NeedForm onSave={create} onCancel={() => setCreating(false)} />}
      {!hasNeeds && !creating && <EmptyState />}
      {hasNeeds && (
        <>
          <StatusFilter needs={needs} value={statusFilter} onChange={setStatusFilter} />
          <NeedList
            needs={needs}
            statusFilter={statusFilter}
            editingId={editingId}
            onEdit={(need) => {
              setCreating(false);
              setNotice(null);
              setEditingId(need.id);
            }}
            onSave={save}
            onCancelEdit={() => setEditingId(null)}
            onChangeStatus={(change) => {
              setNotice(null);
              setPendingChange(change);
            }}
          />
        </>
      )}
      {pendingChange && (
        <StatusChangeDialog
          pendingChange={pendingChange}
          onDone={finishStatusChange}
          onCancel={() => setPendingChange(null)}
        />
      )}
    </section>
  );
}

export function InstitutionNeeds() {
  const { id } = useParams();
  const { institution, needs, setNeeds, errorMessage, loading } = useManagedNeeds(Number(id));

  if (loading) return <output className="block">Carregando necessidades…</output>;
  if (errorMessage) return <NotFound message={errorMessage} />;
  if (!institution) return null;
  return <NeedsManager institution={institution} needs={needs} setNeeds={setNeeds} />;
}
