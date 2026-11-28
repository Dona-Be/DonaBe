import { screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { requestsMade } from "./helpers";
import { CLOSED_AT, NEED, card, filter, loadedCard, openNeeds } from "./needs";

const FULFILL = "POST /api/needs/7/fulfill";
const CLOSE = "POST /api/needs/7/close";

function changedTo(status: string) {
  return { body: { ...NEED, status, closed_at: CLOSED_AT } };
}

function dialog(name?: string) {
  return within(screen.getByRole("alertdialog", { name }));
}

describe("ConfirmDialog", () => {
  it("asks before marking a need as fulfilled and keeps the focus inside", async () => {
    const { fetchMock, user } = openNeeds([NEED], { [FULFILL]: changedTo("fulfilled") });
    const opener = (await loadedCard("Cobertores")).getByRole("button", {
      name: "Marcar como atendida",
    });

    await user.click(opener);
    const asked = dialog("Marcar como atendida?");
    const back = asked.getByRole("button", { name: "Voltar" });
    expect(asked.getByText("“Cobertores” deixa de aparecer para os doadores.")).toBeTruthy();
    expect(document.activeElement).toBe(back);
    await user.tab({ shift: true });
    expect(document.activeElement).toBe(
      asked.getByRole("button", { name: "Marcar como atendida" }),
    );
    await user.tab();
    expect(document.activeElement).toBe(back);
    const overlay = screen.getByRole("alertdialog").parentElement;
    if (!overlay) throw new Error("dialog without overlay");
    await user.click(overlay);
    expect(screen.getByRole("alertdialog")).toBeTruthy();
    await user.click(back);
    expect(screen.queryByRole("alertdialog")).toBeNull();
    expect(document.activeElement).toBe(opener);
    expect(requestsMade(fetchMock)).not.toContain(FULFILL);

    await user.click(opener);
    await user.click(dialog().getByRole("button", { name: "Marcar como atendida" }));

    expect((await screen.findByRole("status")).textContent).toBe(
      "“Cobertores” foi marcada como atendida.",
    );
    expect(document.activeElement).toBe(screen.getByRole("status"));
    expect(screen.queryByRole("alertdialog")).toBeNull();
    expect(filter(/^Abertas/).textContent).toBe("Abertas 0");
    await user.click(filter(/^Atendidas/));
    expect(card("Cobertores").getByText("Atendida em 20/11/2026")).toBeTruthy();
  });

  it("closes a need after confirming", async () => {
    const { user } = openNeeds([NEED], { [CLOSE]: changedTo("closed") });

    await user.click((await loadedCard("Cobertores")).getByRole("button", { name: "Encerrar" }));
    await user.click(dialog("Encerrar necessidade?").getByRole("button", { name: "Encerrar" }));

    expect((await screen.findByRole("status")).textContent).toBe("“Cobertores” foi encerrada.");
    await user.click(filter(/^Encerradas/));
    expect(card("Cobertores").getByText("Encerrada em 20/11/2026")).toBeTruthy();
  });

  it.each(["Marcar como atendida", "Encerrar"])(
    "locks the dialog while %s runs",
    async (action) => {
      const { fetchMock, user } = openNeeds([NEED]);
      await user.click((await loadedCard("Cobertores")).getByRole("button", { name: action }));
      fetchMock.mockReturnValue(new Promise<Response>(() => undefined));
      const confirm = dialog().getByRole("button", { name: action });

      await user.click(confirm);
      await user.keyboard("{Escape}");

      expect(confirm.hasAttribute("disabled")).toBe(true);
      expect(dialog().getByRole("button", { name: "Voltar" }).hasAttribute("disabled")).toBe(true);
      expect(screen.getByRole("alertdialog")).toBeTruthy();
    },
  );

  it("shows why a status change failed and closes on Escape", async () => {
    const notOpen = {
      status: 409,
      body: { detail: "Apenas necessidades abertas podem mudar de status." },
    };
    const { user } = openNeeds([NEED], { [CLOSE]: notOpen });

    await user.click((await loadedCard("Cobertores")).getByRole("button", { name: "Encerrar" }));
    await user.click(dialog().getByRole("button", { name: "Encerrar" }));

    expect((await dialog().findByRole("alert")).textContent).toBe(notOpen.body.detail);
    await user.keyboard("{Escape}");
    expect(screen.queryByRole("alertdialog")).toBeNull();
    expect(filter(/^Abertas/).textContent).toBe("Abertas 1");
  });
});
