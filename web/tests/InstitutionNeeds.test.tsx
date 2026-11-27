import { screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import {
  DONOR,
  INSTITUTION,
  MANAGER_SESSION,
  bodySent,
  field,
  mockFetch,
  renderApp,
  requestsMade,
} from "./helpers";

const PAGE = "/instituicoes/1/necessidades";
const MY_INSTITUTIONS = { "GET /api/institutions/me": { body: [INSTITUTION] } };
const LIST = "GET /api/institutions/1/needs";
const NEED = {
  id: 7,
  title: "Cobertores",
  description: "Cobertores de casal para o inverno.",
  quantity: "20 unidades",
  status: "open",
  closed_at: null,
};
const FULFILLED = {
  ...NEED,
  id: 8,
  title: "Fraldas",
  quantity: null,
  status: "fulfilled",
  closed_at: "2026-11-20T15:00:00Z",
};
const CLOSED = {
  ...NEED,
  id: 9,
  title: "Leite em pó",
  status: "closed",
  closed_at: FULFILLED.closed_at,
};

function withNeeds(needs: unknown[], responses: Parameters<typeof mockFetch>[0] = {}) {
  return mockFetch({
    ...MANAGER_SESSION,
    ...MY_INSTITUTIONS,
    [LIST]: { body: needs },
    ...responses,
  });
}

function card(title: string) {
  return within(screen.getByRole("article", { name: title }));
}

async function loadedCard(title: string) {
  return within(await screen.findByRole("article", { name: title }));
}

function filter(name: RegExp) {
  return screen.getByRole("button", { name });
}

describe("InstitutionNeeds", () => {
  it("shows a clear empty state and publishes the first need", async () => {
    const fetchMock = withNeeds([], {
      "POST /api/institutions/1/needs": { status: 201, body: NEED },
    });
    const user = renderApp(PAGE);

    expect(
      await screen.findByRole("heading", { level: 1, name: "Necessidades – Aacd Ibirapuera" }),
    ).toBeTruthy();
    expect(screen.getByRole("link", { name: "Ver página pública" }).getAttribute("href")).toBe(
      "/instituicoes/1",
    );
    expect(
      screen.getByRole("heading", { name: "Nenhuma necessidade publicada ainda" }),
    ).toBeTruthy();
    expect(screen.queryByRole("group", { name: "Filtrar por status" })).toBeNull();
    await user.click(screen.getByRole("button", { name: "Nova necessidade" }));

    const form = within(screen.getByRole("form", { name: "Nova necessidade" }));
    await user.type(field("Título"), "  Cobertores ");
    await user.type(form.getByLabelText("Descrição"), NEED.description);
    await user.type(field("Quantidade (opcional)"), NEED.quantity);
    await user.click(form.getByRole("button", { name: "Publicar necessidade" }));

    expect((await screen.findByRole("status")).textContent).toBe("“Cobertores” foi publicada.");
    expect(bodySent(fetchMock, "POST /api/institutions/1/needs")).toEqual({
      title: "Cobertores",
      description: NEED.description,
      quantity: NEED.quantity,
    });
    expect(screen.queryByRole("form", { name: "Nova necessidade" })).toBeNull();
    expect(card("Cobertores").getByText("Quantidade: 20 unidades")).toBeTruthy();
    expect(filter(/^Abertas/).getAttribute("aria-pressed")).toBe("true");
  });

  it("lists the needs by status", async () => {
    withNeeds([NEED, FULFILLED, CLOSED]);
    const user = renderApp(PAGE);

    expect(await screen.findByRole("article", { name: "Cobertores" })).toBeTruthy();
    expect(filter(/^Abertas/).textContent).toBe("Abertas 1");
    expect(filter(/^Atendidas/).textContent).toBe("Atendidas 1");
    expect(filter(/^Encerradas/).textContent).toBe("Encerradas 1");
    await user.click(screen.getByRole("button", { name: "Nova necessidade" }));
    expect(screen.getByRole("form", { name: "Nova necessidade" })).toBeTruthy();
    await user.click(screen.getByRole("button", { name: "Cancelar" }));
    expect(screen.queryByRole("article", { name: "Fraldas" })).toBeNull();

    await user.click(filter(/^Atendidas/));
    const fulfilled = card("Fraldas");
    expect(fulfilled.getByText("Atendida")).toBeTruthy();
    expect(fulfilled.getByText("Atendida em 20/11/2026")).toBeTruthy();
    expect(fulfilled.queryByText(/^Quantidade/)).toBeNull();
    expect(fulfilled.queryByRole("button")).toBeNull();
    expect(screen.queryByRole("article", { name: "Cobertores" })).toBeNull();

    await user.click(filter(/^Encerradas/));
    expect(card("Leite em pó").getByText("Encerrada em 20/11/2026")).toBeTruthy();
  });

  it("says when there is nothing in a status", async () => {
    withNeeds([FULFILLED]);
    const user = renderApp(PAGE);

    expect(await screen.findByText(/^Nenhuma necessidade aberta/)).toBeTruthy();
    await user.click(filter(/^Encerradas/));
    expect(screen.getByText("Nenhuma necessidade encerrada.")).toBeTruthy();
  });

  it("edits a need and removes its quantity if left empty", async () => {
    const edited = { ...NEED, title: "Cobertores de casal", quantity: null };
    const fetchMock = withNeeds([NEED], { "PATCH /api/needs/7": { body: edited } });
    const user = renderApp(PAGE);

    await user.click((await loadedCard("Cobertores")).getByRole("button", { name: "Editar" }));
    const form = within(screen.getByRole("form", { name: "Editar necessidade" }));
    expect(form.getByLabelText<HTMLTextAreaElement>("Descrição").value).toBe(NEED.description);
    await user.clear(field("Título"));
    await user.type(field("Título"), edited.title);
    await user.clear(field("Quantidade (opcional)"));
    await user.click(form.getByRole("button", { name: "Salvar alterações" }));

    expect((await screen.findByRole("status")).textContent).toBe("Alterações salvas.");
    expect(bodySent(fetchMock, "PATCH /api/needs/7")).toEqual({
      title: edited.title,
      description: NEED.description,
      quantity: "",
    });
    expect(card("Cobertores de casal").queryByText(/^Quantidade/)).toBeNull();
  });

  it("asks before marking a need as fulfilled", async () => {
    const fetchMock = withNeeds([NEED], {
      "POST /api/needs/7/fulfill": {
        body: { ...NEED, status: "fulfilled", closed_at: FULFILLED.closed_at },
      },
    });
    const user = renderApp(PAGE);

    await user.click(
      (await loadedCard("Cobertores")).getByRole("button", { name: "Marcar como atendida" }),
    );
    let dialog = within(screen.getByRole("alertdialog", { name: "Marcar como atendida?" }));
    expect(dialog.getByText(/“Cobertores” deixa de aparecer para os doadores/)).toBeTruthy();
    await user.click(dialog.getByRole("button", { name: "Voltar" }));
    expect(screen.queryByRole("alertdialog")).toBeNull();

    await user.click(card("Cobertores").getByRole("button", { name: "Marcar como atendida" }));
    const backdrop = screen.getByRole("alertdialog").parentElement;
    if (!backdrop) throw new Error("dialog without backdrop");
    await user.click(backdrop);
    expect(screen.queryByRole("alertdialog")).toBeNull();
    expect(requestsMade(fetchMock)).not.toContain("POST /api/needs/7/fulfill");

    await user.click(card("Cobertores").getByRole("button", { name: "Marcar como atendida" }));
    dialog = within(screen.getByRole("alertdialog"));
    await user.click(dialog.getByRole("button", { name: "Marcar como atendida" }));

    expect((await screen.findByRole("status")).textContent).toBe(
      "“Cobertores” foi marcada como atendida.",
    );
    expect(screen.queryByRole("alertdialog")).toBeNull();
    expect(filter(/^Abertas/).textContent).toBe("Abertas 0");
    await user.click(filter(/^Atendidas/));
    expect(card("Cobertores").getByText("Atendida em 20/11/2026")).toBeTruthy();
  });

  it("asks before closing a need and shows why it failed", async () => {
    const notOpen = {
      status: 409,
      body: { detail: "Apenas necessidades abertas podem mudar de status." },
    };
    withNeeds([NEED], { "POST /api/needs/7/close": notOpen });
    const user = renderApp(PAGE);

    await user.click((await loadedCard("Cobertores")).getByRole("button", { name: "Encerrar" }));
    const dialog = within(screen.getByRole("alertdialog", { name: "Encerrar necessidade?" }));
    await user.click(dialog.getByRole("button", { name: "Encerrar" }));

    expect((await dialog.findByRole("alert")).textContent).toBe(notOpen.body.detail);
    await user.keyboard("{Escape}");
    expect(screen.queryByRole("alertdialog")).toBeNull();
    expect(card("Cobertores").getByText("Aberta")).toBeTruthy();
  });

  it("is reachable from the manager's institutions", async () => {
    withNeeds([NEED]);
    const user = renderApp("/instituicoes");

    await user.click(await screen.findByRole("link", { name: "Necessidades" }));

    expect(await screen.findByRole("article", { name: "Cobertores" })).toBeTruthy();
  });

  it("does not open the needs of another manager's institution", async () => {
    const fetchMock = withNeeds([]);

    renderApp("/instituicoes/2/necessidades");

    expect((await screen.findByRole("alert")).textContent).toBe(
      "Instituição não encontrada entre as suas instituições.",
    );
    expect(requestsMade(fetchMock)).not.toContain("GET /api/institutions/2/needs");
  });

  it("keeps the needs page restricted to managers", async () => {
    mockFetch({ "GET /api/profiles/me": { body: DONOR } });

    renderApp(PAGE);

    expect(await screen.findByRole("heading", { name: "Olá, Maria Silva" })).toBeTruthy();
    expect(screen.queryByRole("heading", { name: /^Necessidades/ })).toBeNull();
  });
});
