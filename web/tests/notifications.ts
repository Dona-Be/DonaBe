import { screen } from "@testing-library/react";
import type { Notification } from "../src/api/notifications";
import { mockFetch, renderApp, USER } from "./helpers";

export const DONOR_SESSION = { "GET /api/profiles/me": { body: USER } };
export const UNREAD_COUNT = "GET /api/notifications/unread-count";
export const FIRST_PAGE = "GET /api/notifications?page=1";
export const SECOND_PAGE = "GET /api/notifications?page=2";
export const READ_ALL = "POST /api/notifications/read-all";
const MINUTE = 60_000;

function minutesAgo(minutes: number): string {
  return new Date(Date.now() - minutes * MINUTE).toISOString();
}

export function notification(id: number, changes: Partial<Notification> = {}): Notification {
  return {
    id,
    type: "intent_status_changed",
    message: `Notificação ${String(id)}`,
    donation_intent_id: 100 + id,
    read_at: null,
    created_at: minutesAgo(5),
    ...changes,
  };
}

export const UNREAD = notification(1, {
  message: "Sua doação para a necessidade Ração mudou para Em contato.",
});
export const READ = notification(2, {
  message: "Sua doação para a necessidade Cobertores mudou para Recebida.",
  read_at: minutesAgo(1),
  created_at: minutesAgo(3 * 24 * 60),
});
export const READ_ONE = `POST /api/notifications/${String(UNREAD.id)}/read`;

export function count(value: number) {
  return { body: { count: value } };
}

type Responses = Parameters<typeof mockFetch>[0];

export async function openBell(extra: Responses, session = DONOR_SESSION) {
  const responses: Responses = { ...session, ...extra };
  const fetchMock = mockFetch(responses);
  const user = renderApp("/");
  await user.click(await screen.findByRole("button", { name: /^Notificações/ }));
  const panel = await screen.findByRole("region", { name: "Notificações" });
  return { fetchMock, user, panel, responses };
}
