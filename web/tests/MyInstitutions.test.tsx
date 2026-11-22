import { screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import {
  DONOR,
  INSTITUTION,
  MANAGER_SESSION,
  bodySent,
  field,
  mockFetch,
  renderApp,
} from "./helpers";

describe("MyInstitutions", () => {
  it("lists a manager's institutions and lets them edit their own details", async () => {
    const fetchMock = mockFetch({
      ...MANAGER_SESSION,
      "GET /api/institutions/me": { body: [INSTITUTION] },
      "PATCH /api/institutions/1": { body: { ...INSTITUTION, trade_name: "AACD atualizada" } },
    });
    const user = renderApp("/instituicoes");

    expect(await screen.findByText("Aacd Ibirapuera")).toBeTruthy();
    expect(screen.getByRole("link", { name: "Minhas instituições" })).toBeTruthy();
    await user.click(screen.getByRole("link", { name: "Editar" }));

    expect(await screen.findByRole("heading", { name: "Editar instituição" })).toBeTruthy();
    expect(screen.getByText(INSTITUTION.cnpj)).toBeTruthy();
    expect(screen.getByText(INSTITUTION.legal_name)).toBeTruthy();
    expect(screen.queryByLabelText("CNPJ")).toBeNull();
    expect(field("CEP").value).toBe("04027-000");
    expect(screen.getByText(/04027-000$/)).toBeTruthy();
    expect(screen.getByRole("link", { name: "Cancelar" }).getAttribute("href")).toBe(
      "/instituicoes",
    );
    const tradeName = screen.getByLabelText("Nome fantasia");
    await user.clear(tradeName);
    await user.type(tradeName, "AACD atualizada");
    await user.click(screen.getByRole("button", { name: "Salvar alterações" }));

    expect(await screen.findByRole("heading", { name: "Minhas instituições" })).toBeTruthy();
    expect(bodySent(fetchMock, "PATCH /api/institutions/1")).toEqual({
      trade_name: "AACD atualizada",
      description: INSTITUTION.description,
      causes: INSTITUTION.causes,
      phone: INSTITUTION.phone,
      contact_email: INSTITUTION.contact_email,
      website: INSTITUTION.website,
      instagram: INSTITUTION.instagram,
      facebook: INSTITUTION.facebook,
      street: INSTITUTION.street,
      number: INSTITUTION.number,
      complement: "",
      neighborhood: INSTITUTION.neighborhood,
      city: INSTITUTION.city,
      state: INSTITUTION.state,
      postal_code: "04027-000",
    });
  });

  it("does not open an institution of another manager", async () => {
    mockFetch({ ...MANAGER_SESSION, "GET /api/institutions/me": { body: [INSTITUTION] } });

    renderApp("/instituicoes/2/editar");

    expect(
      await screen.findByText("Instituição não encontrada entre as suas instituições."),
    ).toBeTruthy();
    expect(screen.queryByLabelText("Nome fantasia")).toBeNull();
  });

  it("keeps the institution pages restricted to managers", async () => {
    mockFetch({ "GET /api/profiles/me": { body: DONOR } });

    renderApp("/instituicoes");

    expect(await screen.findByRole("heading", { name: "Olá, Maria Silva" })).toBeTruthy();
    expect(screen.queryByRole("heading", { name: "Minhas instituições" })).toBeNull();
    expect(screen.queryByRole("link", { name: "Minhas instituições" })).toBeNull();
  });
});
