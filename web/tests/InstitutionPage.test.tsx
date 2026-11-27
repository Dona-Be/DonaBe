import { screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { DONOR, INSTITUTION, mockFetch, renderApp, requestsMade } from "./helpers";

const DONOR_SESSION = { "GET /api/profiles/me": { body: DONOR } };
const PAGE = "GET /api/institutions/1";
const NEED = {
  id: 1,
  title: "Cobertores",
  description: "Cobertores de casal para o inverno.",
  quantity: "20",
};
const ADDRESS = "Avenida Prof Ascendino Reis, 724, VL Clementino, São Paulo, SP, 04027-000";
const NOT_FOUND = "Instituição não encontrada.";

function link(name: string): string | null {
  return screen.getByRole("link", { name }).getAttribute("href");
}

describe("InstitutionPage", () => {
  it("shows a donor the data, open needs and contacts of an institution", async () => {
    const needs = [NEED, { ...NEED, id: 2, title: "Fraldas", quantity: null }];
    mockFetch({ ...DONOR_SESSION, [PAGE]: { body: { ...INSTITUTION, open_needs: needs } } });

    renderApp("/instituicoes/1");

    expect(await screen.findByRole("heading", { name: "Aacd Ibirapuera" })).toBeTruthy();
    expect(screen.getByText("Associação em São Paulo, SP")).toBeTruthy();
    expect(screen.getByText("Organização sem fins lucrativos")).toBeTruthy();
    expect(screen.getByText(`${INSTITUTION.legal_name}, CNPJ ${INSTITUTION.cnpj}`)).toBeTruthy();
    expect(screen.getByText(INSTITUTION.description)).toBeTruthy();
    const causes = within(screen.getByRole("list", { name: "Causas atendidas" }));
    expect(causes.getAllByRole("listitem").map((cause) => cause.textContent)).toEqual([
      "Saúde",
      "Pessoas com deficiência",
    ]);
    expect(screen.getByRole("heading", { name: "Fraldas" })).toBeTruthy();
    expect(screen.getAllByText(/^Quantidade/).map((line) => line.textContent)).toEqual([
      "Quantidade: 20",
    ]);
    expect(screen.getAllByText(NEED.description)).toHaveLength(2);
    expect(screen.getByText("(11) 2000-0000")).toBeTruthy();
    expect(link("contato@exemplo.org")).toBe("mailto:contato@exemplo.org");
    expect(link("exemplo.org")).toBe(INSTITUTION.website);
    expect(link("instagram.com/exemplo")).toBe(INSTITUTION.instagram);
    expect(link("facebook.com/exemplo")).toBe(INSTITUTION.facebook);
    expect(screen.getByText(ADDRESS)).toBeTruthy();
  });

  it("shows an institution without trade name, causes, contacts or needs", async () => {
    const noContacts = {
      phone: null,
      contact_email: null,
      website: null,
      instagram: null,
      facebook: null,
    };
    const bare = { ...INSTITUTION, ...noContacts, trade_name: null, causes: [], open_needs: [] };
    mockFetch({ ...DONOR_SESSION, [PAGE]: { body: bare } });

    renderApp("/instituicoes/1");

    expect(await screen.findByRole("heading", { name: INSTITUTION.legal_name })).toBeTruthy();
    expect(screen.getByText(`CNPJ ${INSTITUTION.cnpj}`)).toBeTruthy();
    expect(screen.queryByRole("list", { name: "Causas atendidas" })).toBeNull();
    expect(screen.getByText("Nenhuma necessidade aberta no momento.")).toBeTruthy();
    expect(screen.queryByText("Telefone / WhatsApp")).toBeNull();
    expect(screen.queryByText("E-mail")).toBeNull();
    expect(screen.queryAllByRole("link", { name: /exemplo/ })).toEqual([]);
    expect(screen.getByText(ADDRESS)).toBeTruthy();
  });

  it("says when the institution does not exist", async () => {
    const missing = { status: 404, body: { detail: NOT_FOUND } };
    mockFetch({ ...DONOR_SESSION, "GET /api/institutions/2": missing });

    renderApp("/instituicoes/2");

    expect((await screen.findByRole("alert")).textContent).toBe(NOT_FOUND);
  });

  it.each(["abc", "0"])("says institution %s does not exist without asking the API", async (id) => {
    const fetchMock = mockFetch(DONOR_SESSION);

    renderApp(`/instituicoes/${id}`);

    expect((await screen.findByRole("alert")).textContent).toBe(NOT_FOUND);
    const institutionRequests = requestsMade(fetchMock).filter((request) =>
      request.includes("/api/institutions"),
    );
    expect(institutionRequests).toEqual([]);
  });
});
