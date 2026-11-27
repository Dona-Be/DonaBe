import { useCallback, useEffect, useRef, useState, type RefObject } from "react";
import { Link } from "react-router";
import {
  listNotifications,
  markAllNotificationsAsRead,
  markNotificationAsRead,
  NOTIFICATIONS_PAGE_SIZE,
  type Notification,
} from "../api/notifications";
import { useAuth } from "../auth/useAuth";
import { friendlyMessage } from "../errors";
import { formatRelativeTime } from "../format";
import { useAction } from "../hooks/useAction";
import { useUnreadCount } from "../hooks/useUnreadCount";
import { routes } from "../routes";
import type { Role } from "../types/user";
import { ErrorMessage } from "./ErrorMessage";
import { Loading } from "./Loading";

const PANEL_ID = "notification-panel";
const MAX_BADGE_COUNT = 9;
const TEXT_BUTTON_CLASS =
  "cursor-pointer text-sm text-sky-800 underline disabled:cursor-not-allowed disabled:opacity-60";

const intentPageByRole: Record<Role, string> = {
  donor: routes.myDonations,
  manager: routes.receivedIntents,
};

function BellIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" className="h-6 w-6" fill="none">
      <path
        d="M6 8a6 6 0 1 1 12 0c0 7 3 9 3 9H3s3-2 3-9M10.3 21a1.94 1.94 0 0 0 3.4 0"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function bellLabel(count: number): string {
  if (count === 0) return "Notificações";
  return count === 1 ? "Notificações, 1 não lida" : `Notificações, ${String(count)} não lidas`;
}

function withoutRepeated(current: Notification[], next: Notification[]): Notification[] {
  // A notification created between two pages pushes the older ones to the next page.
  const known = new Set(current.map(({ id }) => id));
  return [...current, ...next.filter(({ id }) => !known.has(id))];
}

function markedAsRead(notification: Notification): Notification {
  return { ...notification, read_at: notification.read_at ?? new Date().toISOString() };
}

function useCloseOnOutsideClickOrEscape(
  container: RefObject<HTMLElement | null>,
  open: boolean,
  close: () => void,
) {
  useEffect(() => {
    if (!open) return;
    const closeOnOutsideClick = (event: MouseEvent) => {
      if (!container.current?.contains(event.target as Node)) close();
    };
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") close();
    };
    document.addEventListener("mousedown", closeOnOutsideClick);
    document.addEventListener("keydown", closeOnEscape);
    return () => {
      document.removeEventListener("mousedown", closeOnOutsideClick);
      document.removeEventListener("keydown", closeOnEscape);
    };
  }, [container, open, close]);
}

function useNotificationPages() {
  const [notifications, setNotifications] = useState<Notification[] | null>(null);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    listNotifications(1)
      .then((first) => {
        if (!active) return;
        setNotifications(first);
        setHasMore(first.length === NOTIFICATIONS_PAGE_SIZE);
      })
      .catch((error: unknown) => {
        if (active) setLoadError(friendlyMessage(error));
      });
    return () => {
      active = false;
    };
  }, []);

  async function loadMore() {
    const next = await listNotifications(page + 1);
    setNotifications((current) => withoutRepeated(current ?? [], next));
    setPage(page + 1);
    setHasMore(next.length === NOTIFICATIONS_PAGE_SIZE);
  }

  return { notifications, setNotifications, hasMore, loadError, loadMore };
}

interface NotificationItemProps {
  notification: Notification;
  intentPage: string;
  onOpen: (notification: Notification) => void;
  onMarkAsRead: (notification: Notification) => void;
  pending: boolean;
}

function NotificationItem({
  notification,
  intentPage,
  onOpen,
  onMarkAsRead,
  pending,
}: Readonly<NotificationItemProps>) {
  const unread = notification.read_at === null;
  return (
    <li className={`flex gap-3 p-3 ${unread ? "bg-sky-50" : ""}`}>
      <span
        aria-hidden="true"
        className={`mt-2 h-2 w-2 shrink-0 rounded-full ${unread ? "bg-sky-600" : ""}`}
      />
      <div className="min-w-0 flex-1 space-y-1">
        <Link
          to={`${intentPage}?intencao=${String(notification.donation_intent_id)}`}
          onClick={() => onOpen(notification)}
          className={`block hover:underline ${unread ? "font-semibold" : ""}`}
        >
          {unread && <span className="sr-only">Não lida: </span>}
          {notification.message}
        </Link>
        <div className="flex flex-wrap items-center justify-between gap-2 text-sm text-slate-600">
          <time dateTime={notification.created_at}>
            {formatRelativeTime(notification.created_at)}
          </time>
          {unread && (
            <button
              type="button"
              disabled={pending}
              onClick={() => onMarkAsRead(notification)}
              className={TEXT_BUTTON_CLASS}
            >
              Marcar como lida
            </button>
          )}
        </div>
      </div>
    </li>
  );
}

interface NotificationListProps extends Omit<NotificationItemProps, "notification"> {
  notifications: Notification[] | null;
  loadError: string | null;
}

function NotificationList({
  notifications,
  loadError,
  ...itemProps
}: Readonly<NotificationListProps>) {
  if (loadError) {
    return (
      <div className="p-3">
        <ErrorMessage message={loadError} />
      </div>
    );
  }
  if (notifications === null) return <Loading />;
  if (notifications.length === 0) {
    return <p className="p-6 text-center text-slate-600">Você não tem notificações.</p>;
  }
  return (
    <ul className="divide-y divide-slate-100">
      {notifications.map((notification) => (
        <NotificationItem key={notification.id} notification={notification} {...itemProps} />
      ))}
    </ul>
  );
}

interface NotificationPanelProps {
  intentPage: string;
  onRead: () => void;
  onClose: () => void;
}

function NotificationPanel({ intentPage, onRead, onClose }: Readonly<NotificationPanelProps>) {
  const { notifications, setNotifications, hasMore, loadError, loadMore } = useNotificationPages();
  const { errorMessage, pending, run } = useAction();

  function markAsRead(notification: Notification) {
    run(async () => {
      await markNotificationAsRead(notification.id);
      setNotifications((current) =>
        (current ?? []).map((item) => (item.id === notification.id ? markedAsRead(item) : item)),
      );
      onRead();
    });
  }

  function markAllAsRead() {
    run(async () => {
      await markAllNotificationsAsRead();
      setNotifications((current) => (current ?? []).map(markedAsRead));
      onRead();
    });
  }

  function open(notification: Notification) {
    if (notification.read_at === null) {
      markNotificationAsRead(notification.id)
        .then(onRead)
        .catch(() => undefined);
    }
    onClose();
  }

  return (
    <section
      id={PANEL_ID}
      aria-label="Notificações"
      className="absolute top-full right-0 z-10 mt-2 w-80 max-w-[calc(100vw-2rem)] overflow-hidden rounded-lg border border-slate-200 bg-white text-left shadow-lg"
    >
      <div className="flex items-center justify-between gap-2 border-b border-slate-200 p-3">
        <h2 className="font-bold">Notificações</h2>
        <button
          type="button"
          disabled={pending || !notifications?.some(({ read_at }) => read_at === null)}
          onClick={markAllAsRead}
          className={TEXT_BUTTON_CLASS}
        >
          Marcar todas como lidas
        </button>
      </div>
      <div className="max-h-96 overflow-y-auto">
        {errorMessage && (
          <div className="p-3">
            <ErrorMessage message={errorMessage} />
          </div>
        )}
        <NotificationList
          notifications={notifications}
          loadError={loadError}
          intentPage={intentPage}
          onOpen={open}
          onMarkAsRead={markAsRead}
          pending={pending}
        />
        {hasMore && (
          <div className="border-t border-slate-200 p-3 text-center">
            <button
              type="button"
              disabled={pending}
              onClick={() => run(loadMore)}
              className={TEXT_BUTTON_CLASS}
            >
              Carregar mais
            </button>
          </div>
        )}
      </div>
    </section>
  );
}

export function NotificationBell() {
  const { role } = useAuth();
  const { count, refresh } = useUnreadCount();
  const [open, setOpen] = useState(false);
  const container = useRef<HTMLDivElement>(null);
  const button = useRef<HTMLButtonElement>(null);

  const close = useCallback(() => {
    setOpen(false);
    button.current?.focus();
  }, []);

  useCloseOnOutsideClickOrEscape(container, open, close);

  if (!role) return null;

  function toggle() {
    if (!open) refresh();
    setOpen(!open);
  }

  return (
    <div ref={container} className="relative">
      <button
        ref={button}
        type="button"
        aria-label={bellLabel(count)}
        aria-expanded={open}
        aria-controls={open ? PANEL_ID : undefined}
        onClick={toggle}
        className="relative cursor-pointer rounded-full p-2 text-slate-700 hover:bg-slate-100 focus-visible:outline-2 focus-visible:outline-sky-700"
      >
        <BellIcon />
        {count > 0 && (
          <span
            aria-hidden="true"
            className="absolute -top-0.5 -right-0.5 min-w-5 rounded-full bg-red-600 px-1 text-center text-xs leading-5 font-bold text-white"
          >
            {count > MAX_BADGE_COUNT ? `${String(MAX_BADGE_COUNT)}+` : count}
          </span>
        )}
      </button>
      {open && (
        <NotificationPanel intentPage={intentPageByRole[role]} onRead={refresh} onClose={close} />
      )}
    </div>
  );
}
