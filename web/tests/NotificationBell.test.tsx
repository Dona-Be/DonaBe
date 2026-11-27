import { act, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type { Notification } from "../src/api/notifications";
import { MANAGER_SESSION, mockFetch, renderApp, requestsMade, USER } from "./helpers";

const DONOR_SESSION = { "GET /api/profiles/me": { body: USER } };
const UNREAD_COUNT = "GET /api/notifications/unread-count";
const FIRST_PAGE = "GET /api/notifications?page=1";
const SECOND_PAGE = "GET /api/notifications?page=2";
const READ_ALL = "POST /api/notifications/read-all";
const MINUTE = 60_000;

function minutesAgo(minutes: number): string {
  return new Date(Date.now() - minutes * MINUTE).toISOString();
}

function notification(id: number, changes: Partial<Notification> = {}): Notification {
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

const UNREAD = notification(1, {
  message: "Sua doação para a necessidade Ração mudou para Em contato.",
});
const READ = notification(2, {
  message: "Sua doação para a necessidade Cobertores mudou para Recebida.",
  read_at: minutesAgo(1),
  created_at: minutesAgo(3 * 24 * 60),
});

function count(value: number) {
  return { body: { count: value } };
}

type Responses = Parameters<typeof mockFetch>[0];

async function openBell(extra: Responses, session = DONOR_SESSION) {
  const responses: Responses = { ...session, ...extra };
  const fetchMock = mockFetch(responses);
  const user = renderApp("/");
  await user.click(await screen.findByRole("button", { name: /^Notificações/ }));
  const panel = await screen.findByRole("region", { name: "Notificações" });
  return { fetchMock, user, panel, responses };
}

describe("NotificationBell", () => {
  it("shows how many notifications are unread", async () => {
    mockFetch({ ...DONOR_SESSION, [UNREAD_COUNT]: count(3) });

    renderApp("/");

    const bell = await screen.findByRole("button", { name: "Notificações, 3 não lidas" });
    expect(bell.textContent).toBe("3");
  });

  it("caps the badge at 9+", async () => {
    mockFetch({ ...DONOR_SESSION, [UNREAD_COUNT]: count(12) });

    renderApp("/");

    const bell = await screen.findByRole("button", { name: "Notificações, 12 não lidas" });
    expect(bell.textContent).toBe("9+");
  });

  it("shows no badge when everything is read", async () => {
    mockFetch({ ...DONOR_SESSION, [UNREAD_COUNT]: count(0) });

    renderApp("/");

    const bell = await screen.findByRole("button", { name: "Notificações" });
    expect(bell.textContent).toBe("");
  });

  it("keeps the page working when the count cannot be read", async () => {
    mockFetch({ ...DONOR_SESSION, [UNREAD_COUNT]: { status: 500 } });

    renderApp("/");

    expect(await screen.findByRole("button", { name: "Notificações" })).toBeTruthy();
    expect(screen.queryByRole("alert")).toBeNull();
  });

  it("lists the newest notifications with the unread ones marked", async () => {
    const { panel } = await openBell({
      [UNREAD_COUNT]: count(1),
      [FIRST_PAGE]: { body: [UNREAD, READ] },
    });

    const items = await within(panel).findAllByRole("listitem");
    expect(items).toHaveLength(2);
    expect(items[0]?.textContent).toContain(`Não lida: ${UNREAD.message}`);
    expect(items[0]?.textContent).toContain("há 5 minutos");
    expect(items[1]?.textContent).not.toContain("Não lida");
    expect(items[1]?.textContent).toContain("há 3 dias");
    expect(within(items[1]).queryByRole("button")).toBeNull();
  });

  it("says when there are no notifications", async () => {
    const { panel } = await openBell({ [UNREAD_COUNT]: count(0), [FIRST_PAGE]: { body: [] } });

    expect(await within(panel).findByText("Você não tem notificações.")).toBeTruthy();
    const markAll = within(panel).getByRole("button", { name: "Marcar todas como lidas" });
    expect(markAll.hasAttribute("disabled")).toBe(true);
  });

  it("shows the error when the list cannot be loaded", async () => {
    const { panel } = await openBell({
      [UNREAD_COUNT]: count(1),
      [FIRST_PAGE]: { status: 500, body: { detail: "Falha interna." } },
    });

    expect((await within(panel).findByRole("alert")).textContent).toBe("Falha interna.");
  });

  it("marks one notification as read", async () => {
    const markOne = `POST /api/notifications/${String(UNREAD.id)}/read`;
    const { fetchMock, user, panel, responses } = await openBell({
      [UNREAD_COUNT]: count(1),
      [FIRST_PAGE]: { body: [UNREAD, READ] },
      [markOne]: { status: 204 },
    });
    responses[UNREAD_COUNT] = count(0);

    await user.click(await within(panel).findByRole("button", { name: "Marcar como lida" }));

    expect(await screen.findByRole("button", { name: "Notificações" })).toBeTruthy();
    expect(within(panel).queryByRole("button", { name: "Marcar como lida" })).toBeNull();
    expect(requestsMade(fetchMock).slice(-2)).toEqual([markOne, UNREAD_COUNT]);
  });

  it("marks all notifications as read", async () => {
    const { fetchMock, user, panel, responses } = await openBell({
      [UNREAD_COUNT]: count(2),
      [FIRST_PAGE]: { body: [UNREAD, notification(3)] },
      [READ_ALL]: { status: 204 },
    });
    await within(panel).findAllByRole("listitem");
    responses[UNREAD_COUNT] = count(0);

    await user.click(within(panel).getByRole("button", { name: "Marcar todas como lidas" }));

    expect(await screen.findByRole("button", { name: "Notificações" })).toBeTruthy();
    expect(within(panel).queryByText(/Não lida/)).toBeNull();
    expect(requestsMade(fetchMock).slice(-2)).toEqual([READ_ALL, UNREAD_COUNT]);
  });

  it("shows the error when marking as read fails", async () => {
    const { user, panel } = await openBell({
      [UNREAD_COUNT]: count(1),
      [FIRST_PAGE]: { body: [UNREAD] },
      [READ_ALL]: { status: 500, body: { detail: "Falha interna." } },
    });
    await within(panel).findAllByRole("listitem");

    await user.click(within(panel).getByRole("button", { name: "Marcar todas como lidas" }));

    expect((await within(panel).findByRole("alert")).textContent).toBe("Falha interna.");
    expect(screen.getByRole("button", { name: "Notificações, 1 não lida" })).toBeTruthy();
  });

  it.each([
    [DONOR_SESSION, "/minhas-doacoes?intencao=101"],
    [MANAGER_SESSION, "/interesses-recebidos?intencao=101"],
  ])("links each notification to its donation intent", async (session, href) => {
    const { panel } = await openBell(
      { [UNREAD_COUNT]: count(1), [FIRST_PAGE]: { body: [UNREAD] } },
      session,
    );

    const link = await within(panel).findByRole("link", { name: /^Não lida:\s*Sua doação/ });
    expect(link.getAttribute("href")).toBe(href);
  });

  it("marks a notification as read and closes the list when it is opened", async () => {
    const markOne = `POST /api/notifications/${String(UNREAD.id)}/read`;
    const { fetchMock, user, panel } = await openBell({
      [UNREAD_COUNT]: count(1),
      [FIRST_PAGE]: { body: [UNREAD] },
      [markOne]: { status: 204 },
    });

    await user.click(await within(panel).findByRole("link", { name: /Ração/ }));

    expect(screen.queryByRole("region", { name: "Notificações" })).toBeNull();
    expect(requestsMade(fetchMock)).toContain(markOne);
  });

  it("loads the next page when the first one is full", async () => {
    const firstPage = Array.from({ length: 20 }, (_, index) => notification(index + 1));
    const { user, panel } = await openBell({
      [UNREAD_COUNT]: count(21),
      [FIRST_PAGE]: { body: firstPage },
      // The newest one came back again because a new notification arrived in between.
      [SECOND_PAGE]: { body: [notification(20), notification(21)] },
    });

    await user.click(await within(panel).findByRole("button", { name: "Carregar mais" }));

    expect(await within(panel).findByText("Notificação 21")).toBeTruthy();
    expect(within(panel).getAllByRole("listitem")).toHaveLength(21);
    expect(within(panel).queryByRole("button", { name: "Carregar mais" })).toBeNull();
  });

  it("closes on Escape and gives the focus back to the bell", async () => {
    const { user } = await openBell({ [UNREAD_COUNT]: count(0), [FIRST_PAGE]: { body: [] } });

    await user.keyboard("{Escape}");

    expect(screen.queryByRole("region", { name: "Notificações" })).toBeNull();
    expect(document.activeElement?.getAttribute("aria-label")).toBe("Notificações");
  });

  it("closes when clicking outside", async () => {
    const { user } = await openBell({ [UNREAD_COUNT]: count(0), [FIRST_PAGE]: { body: [] } });

    await user.click(screen.getByRole("heading", { name: "Olá, Maria Silva" }));

    expect(screen.queryByRole("region", { name: "Notificações" })).toBeNull();
  });

  it("ignores a count that left before marking everything as read", async () => {
    const responses = {
      ...DONOR_SESSION,
      [UNREAD_COUNT]: count(2),
      [FIRST_PAGE]: { body: [UNREAD, notification(3)] },
      [READ_ALL]: { status: 204 },
    };
    const fetchMock = mockFetch(responses);
    const user = renderApp("/");
    const bell = await screen.findByRole("button", { name: "Notificações, 2 não lidas" });
    let answerOldCount: (response: Response) => void = () => undefined;
    fetchMock.mockReturnValueOnce(new Promise((resolve) => (answerOldCount = resolve)));

    await user.click(bell);
    const panel = await screen.findByRole("region", { name: "Notificações" });
    await within(panel).findAllByRole("listitem");
    responses[UNREAD_COUNT] = count(0);
    await user.click(within(panel).getByRole("button", { name: "Marcar todas como lidas" }));
    await screen.findByRole("button", { name: "Notificações" });
    await act(async () => {
      answerOldCount(Response.json({ count: 2 }));
      await new Promise((resolve) => setTimeout(resolve));
    });

    expect(screen.getByRole("button", { name: "Notificações" })).toBeTruthy();
  });
});
