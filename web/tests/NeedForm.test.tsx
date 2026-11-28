import { screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { bodySent, field, requestsMade } from "./helpers";
import { FULFILLED, NEED, card, filter, loadedCard, openNeeds } from "./needs";

const CREATE = "POST /api/institutions/1/needs";
const EDIT = "PATCH /api/needs/7";

describe("NeedForm", () => {
  it("publishes a need and shows the open needs again", async () => {
    const created = { ...NEED, id: 10, title: "Arroz", description: "Tipo 1.", quantity: "5 kg" };
    const { fetchMock, user } = openNeeds([FULFILLED], {
      [CREATE]: { status: 201, body: created },
    });

    await user.click(await screen.findByRole("button", { name: /^Atendidas/ }));
    await user.click(screen.getByRole("button", { name: "Nova necessidade" }));
    const form = within(screen.getByRole("form", { name: "Nova necessidade" }));
    await user.type(field("Título"), created.title);
    await user.type(form.getByLabelText("Descrição"), created.description);
    await user.type(field("Quantidade (opcional)"), created.quantity);
    await user.click(form.getByRole("button", { name: "Publicar necessidade" }));

    expect((await screen.findByRole("status")).textContent).toBe("“Arroz” foi publicada.");
    expect(document.activeElement).toBe(screen.getByRole("status"));
    expect(bodySent(fetchMock, CREATE)).toEqual({
      title: created.title,
      description: created.description,
      quantity: created.quantity,
    });
    expect(screen.queryByRole("form", { name: "Nova necessidade" })).toBeNull();
    expect(filter(/^Abertas/).getAttribute("aria-pressed")).toBe("true");
    expect(card("Arroz").getByText("Quantidade: 5 kg")).toBeTruthy();
  });

  it("edits a need and removes its quantity if left empty", async () => {
    const edited = { ...NEED, title: "Cobertores de casal", quantity: null };
    const { fetchMock, user } = openNeeds([NEED], { [EDIT]: { body: edited } });

    await user.click((await loadedCard("Cobertores")).getByRole("button", { name: "Editar" }));
    await user.click(screen.getByRole("button", { name: "Cancelar" }));
    expect(screen.queryByRole("form", { name: "Editar necessidade" })).toBeNull();

    await user.click(card("Cobertores").getByRole("button", { name: "Editar" }));
    const form = within(screen.getByRole("form", { name: "Editar necessidade" }));
    expect(form.getByLabelText<HTMLTextAreaElement>("Descrição").value).toBe(NEED.description);
    await user.clear(field("Título"));
    await user.type(field("Título"), edited.title);
    await user.clear(field("Quantidade (opcional)"));
    await user.click(form.getByRole("button", { name: "Salvar alterações" }));

    expect((await screen.findByRole("status")).textContent).toBe("Alterações salvas.");
    expect(requestsMade(fetchMock).filter((key) => key === EDIT)).toHaveLength(1);
    expect(bodySent(fetchMock, EDIT)).toEqual({
      title: edited.title,
      description: NEED.description,
      quantity: "",
    });
    expect(card("Cobertores de casal").queryByText(/^Quantidade/)).toBeNull();
  });

  it("shows why a need could not be saved", async () => {
    const refused = {
      status: 403,
      body: { detail: "Apenas o gestor da instituição pode alterar esta necessidade." },
    };
    const { user } = openNeeds([NEED], { [EDIT]: refused });

    await user.click((await loadedCard("Cobertores")).getByRole("button", { name: "Editar" }));
    const form = within(screen.getByRole("form", { name: "Editar necessidade" }));
    await user.click(form.getByRole("button", { name: "Salvar alterações" }));

    expect((await form.findByRole("alert")).textContent).toBe(refused.body.detail);
    expect(screen.queryByRole("status")).toBeNull();
  });
});
