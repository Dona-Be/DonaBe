import { screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { requestsMade } from "./helpers";
import {
  count,
  FIRST_PAGE,
  notification,
  openBell,
  READ,
  READ_ALL,
  READ_ONE,
  SECOND_PAGE,
  UNREAD,
  UNREAD_COUNT,
} from "./notifications";

describe("NotificationPanel", () => {
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
    const { fetchMock, user, panel, responses } = await openBell({
      [UNREAD_COUNT]: count(2),
      [FIRST_PAGE]: { body: [UNREAD, notification(3)] },
      [READ_ONE]: { status: 204 },
    });
    const [first] = await within(panel).findAllByRole("listitem");
    responses[UNREAD_COUNT] = count(1);

    await user.click(within(first).getByRole("button", { name: "Marcar como lida" }));

    expect(await screen.findByRole("button", { name: "Notificações, 1 não lida" })).toBeTruthy();
    expect(within(panel).getAllByRole("button", { name: "Marcar como lida" })).toHaveLength(1);
    expect(requestsMade(fetchMock).slice(-2)).toEqual([READ_ONE, UNREAD_COUNT]);
  });

  it("marks all notifications as read", async () => {
    const { fetchMock, user, panel, responses } = await openBell({
      [UNREAD_COUNT]: count(2),
      [FIRST_PAGE]: { body: [UNREAD, notification(3)] },
      [READ_ALL]: { status: 204 },
    });
    await within(panel).findAllByRole("listitem");
    responses[UNREAD_COUNT] = count(0);
    const markAll = within(panel).getByRole("button", { name: "Marcar todas como lidas" });

    await user.click(markAll);

    expect(await screen.findByRole("button", { name: "Notificações" })).toBeTruthy();
    expect(within(panel).queryByText(/Não lida/)).toBeNull();
    expect(markAll.hasAttribute("disabled")).toBe(true);
    expect(requestsMade(fetchMock).slice(-2)).toEqual([READ_ALL, UNREAD_COUNT]);
  });

  it("lets mark all as read when the count could not be read", async () => {
    const { panel } = await openBell({
      [UNREAD_COUNT]: { status: 500 },
      [FIRST_PAGE]: { body: [UNREAD] },
    });
    await within(panel).findAllByRole("listitem");

    const markAll = within(panel).getByRole("button", { name: "Marcar todas como lidas" });
    expect(markAll.hasAttribute("disabled")).toBe(false);
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
});
