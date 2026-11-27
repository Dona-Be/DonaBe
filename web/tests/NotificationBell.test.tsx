import { act, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { MANAGER_SESSION, mockFetch, renderApp, requestsMade } from "./helpers";
import {
  count,
  DONOR_SESSION,
  FIRST_PAGE,
  notification,
  openBell,
  READ,
  READ_ALL,
  READ_ONE,
  UNREAD,
  UNREAD_COUNT,
} from "./notifications";

describe("NotificationBell", () => {
  it.each([
    [3, "Notificações, 3 não lidas", "3"],
    [12, "Notificações, 12 não lidas", "9+"],
    [0, "Notificações", ""],
  ])("shows %i unread notifications on the bell", async (unread, label, badge) => {
    mockFetch({ ...DONOR_SESSION, [UNREAD_COUNT]: count(unread) });

    renderApp("/");

    const bell = await screen.findByRole("button", { name: label });
    expect(bell.textContent).toBe(badge);
  });

  it("keeps the page working when the count cannot be read", async () => {
    mockFetch({ ...DONOR_SESSION, [UNREAD_COUNT]: { status: 500 } });

    renderApp("/");

    expect(await screen.findByRole("button", { name: "Notificações" })).toBeTruthy();
    expect(screen.queryByRole("alert")).toBeNull();
  });

  it("reads the count again when the bell is opened", async () => {
    const responses = { ...DONOR_SESSION, [UNREAD_COUNT]: count(1), [FIRST_PAGE]: { body: [] } };
    mockFetch(responses);
    const user = renderApp("/");
    const bell = await screen.findByRole("button", { name: "Notificações, 1 não lida" });
    responses[UNREAD_COUNT] = count(2);

    await user.click(bell);

    expect(await screen.findByRole("button", { name: "Notificações, 2 não lidas" })).toBeTruthy();
  });

  it("closes on Escape and gives the focus back to the bell", async () => {
    const { user, panel } = await openBell({
      [UNREAD_COUNT]: count(1),
      [FIRST_PAGE]: { body: [UNREAD] },
    });
    await within(panel).findAllByRole("listitem");
    await user.tab();

    await user.keyboard("{Escape}");

    expect(screen.queryByRole("region", { name: "Notificações" })).toBeNull();
    expect(document.activeElement?.getAttribute("aria-label")).toBe("Notificações, 1 não lida");
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

  it("marks only unread notifications as read when opened and closes the list", async () => {
    const { fetchMock, user, panel } = await openBell({
      [UNREAD_COUNT]: count(1),
      [FIRST_PAGE]: { body: [UNREAD, READ] },
      [READ_ONE]: { status: 204 },
    });

    await user.click(await within(panel).findByRole("link", { name: /Ração/ }));
    await user.click(screen.getByRole("button", { name: /^Notificações/ }));
    await user.click(await screen.findByRole("link", { name: /Cobertores/ }));

    expect(screen.queryByRole("region", { name: "Notificações" })).toBeNull();
    expect(requestsMade(fetchMock).filter((request) => request.startsWith("POST"))).toEqual([
      READ_ONE,
    ]);
  });
});
