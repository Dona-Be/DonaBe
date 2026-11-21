import { screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { DONOR, MANAGER, mockFetch, renderApp, bodySent, requestsMade } from "./helpers";

const CNPJ = "60979457000111";
const LOOKUP = `GET /api/institutions/lookup?cnpj=${CNPJ}`;
const PREVIEW = {
  type: "association",
  cnpj: CNPJ,
  legal_name: "ASSOCIACAO DE ASSISTENCIA A CRIANCA DEFICIENTE",
  trade_name: "Aacd Ibirapuera",
  street: "Avenida Prof Ascendino Reis",
  number: "724",
  complement: null,
  neighborhood: "VL Clementino",
  city: "São Paulo",
  state: "SP",
  postal_code: "04027000",
  verdict: "nonprofit",
  reasons: [
    "OK - Situação cadastral: Ativa",
    "OK - Natureza jurídica: 3999 - Associação Privada",
    "NÃO - Atividade principal: 8630501 - Atividade médica ambulatorial",
  ],
};
const INSTITUTION = {
  ...PREVIEW,
  id: 1,
  description: "Reabilitação de crianças com deficiência.",
  causes: ["health", "people_with_disabilities"],
  phone: "1120000000",
  contact_email: "contato@exemplo.org",
  website: "https://exemplo.org",
  instagram: "https://instagram.com/exemplo",
  facebook: "https://facebook.com/exemplo",
};
const MANAGER_SESSION = { "GET /api/profiles/me": { body: MANAGER } };

describe("institution registration", () => {
  it("previews official CNPJ data and submits the completed institution", async () => {
    const fetchMock = mockFetch({
      ...MANAGER_SESSION,
      [LOOKUP]: { body: PREVIEW },
      "POST /api/institutions": { status: 201, body: INSTITUTION },
      "GET /api/institutions/me": { body: [INSTITUTION] },
    });
    const user = renderApp("/instituicoes/nova");

    await user.type(await screen.findByLabelText("CNPJ"), CNPJ);
    await user.click(screen.getByRole("button", { name: "Consultar CNPJ" }));

    expect(await screen.findByText(PREVIEW.legal_name)).toBeTruthy();
    expect(screen.getByText("Associação")).toBeTruthy();
    expect(screen.getByText("Organização sem fins lucrativos")).toBeTruthy();
    expect(screen.getByText(PREVIEW.reasons[2])).toBeTruthy();

    await user.click(screen.getByRole("button", { name: "Continuar para os detalhes" }));
    const tradeName = screen.getByLabelText("Nome fantasia");
    await user.clear(tradeName);
    await user.type(tradeName, "AACD");
    await user.type(screen.getByLabelText("Descrição"), "Reabilitação e inclusão.");
    await user.click(screen.getByRole("checkbox", { name: "Animais" }));
    await user.type(screen.getByLabelText("E-mail de contato (opcional)"), "contato@aacd.org.br");
    await user.click(screen.getByRole("button", { name: "Cadastrar instituição" }));

    expect(await screen.findByRole("heading", { name: "Minhas instituições" })).toBeTruthy();
    expect(bodySent(fetchMock, "POST /api/institutions")).toEqual({
      cnpj: CNPJ,
      trade_name: "AACD",
      description: "Reabilitação e inclusão.",
      causes: ["animals"],
      phone: "",
      contact_email: "contato@aacd.org.br",
      website: "",
      instagram: "",
      facebook: "",
      street: "Avenida Prof Ascendino Reis",
      number: "724",
      complement: "",
      neighborhood: "VL Clementino",
      city: "São Paulo",
      state: "SP",
      postal_code: "04027-000",
    });
    expect(requestsMade(fetchMock)).toContain(LOOKUP);
  });

  it.each([
    ["CNPJ inválido", 422, "O CNPJ informado é inválido."],
    ["CNPJ inativo", 422, "Não é possível cadastrar um CNPJ que não está ativo."],
    ["CNPJ já cadastrado", 409, "Já existe uma instituição cadastrada com o CNPJ 60979457000111."],
    [
      "natureza jurídica não suportada",
      422,
      "Não é possível cadastrar instituições com a natureza jurídica 2062 - Sociedade Empresária Limitada.",
    ],
  ])("shows a clear message when the %s is refused", async (_cause, status, detail) => {
    mockFetch({
      ...MANAGER_SESSION,
      [LOOKUP]: { status, body: { detail } },
    });
    const user = renderApp("/instituicoes/nova");

    await user.type(await screen.findByLabelText("CNPJ"), CNPJ);
    await user.click(screen.getByRole("button", { name: "Consultar CNPJ" }));

    expect((await screen.findByRole("alert")).textContent).toBe(detail);
    expect(screen.getByLabelText("CNPJ")).toBeTruthy();
  });
});

describe("my institutions", () => {
  it("lists a manager's institutions and lets them edit their own details", async () => {
    const fetchMock = mockFetch({
      ...MANAGER_SESSION,
      "GET /api/institutions/me": { body: [INSTITUTION] },
      "PATCH /api/institutions/1": { body: { ...INSTITUTION, trade_name: "AACD atualizada" } },
    });
    const user = renderApp("/instituicoes");

    expect(await screen.findByText("Aacd Ibirapuera")).toBeTruthy();
    await user.click(screen.getByRole("link", { name: "Editar" }));

    expect(await screen.findByRole("heading", { name: "Editar instituição" })).toBeTruthy();
    expect(screen.getByText(PREVIEW.cnpj)).toBeTruthy();
    expect(screen.getByText(PREVIEW.legal_name)).toBeTruthy();
    expect(screen.queryByLabelText("CNPJ")).toBeNull();
    const tradeName = screen.getByLabelText("Nome fantasia");
    await user.clear(tradeName);
    await user.type(tradeName, "AACD atualizada");
    await user.click(screen.getByRole("button", { name: "Salvar alterações" }));

    expect(await screen.findByRole("heading", { name: "Minhas instituições" })).toBeTruthy();
    expect(bodySent(fetchMock, "PATCH /api/institutions/1")).toMatchObject({
      trade_name: "AACD atualizada",
      description: INSTITUTION.description,
      causes: INSTITUTION.causes,
    });
  });

  it("keeps the institution pages restricted to managers", async () => {
    mockFetch({ "GET /api/profiles/me": { body: DONOR } });

    renderApp("/instituicoes");

    expect(await screen.findByRole("heading", { name: "Olá, Maria Silva" })).toBeTruthy();
    expect(screen.queryByRole("heading", { name: "Minhas instituições" })).toBeNull();
  });
});
