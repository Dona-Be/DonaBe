import { screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import {
  INSTITUTION,
  INSTITUTION_PREVIEW,
  MANAGER_SESSION,
  bodySent,
  field,
  mockFetch,
  renderApp,
  requestsMade,
} from "./helpers";

const CNPJ = INSTITUTION_PREVIEW.cnpj;
const LOOKUP = `GET /api/institutions/lookup?cnpj=${CNPJ}`;

async function lookUpCnpj(responses: Parameters<typeof mockFetch>[0]) {
  const fetchMock = mockFetch({ ...MANAGER_SESSION, ...responses });
  const user = renderApp("/instituicoes/nova");
  await user.type(await screen.findByLabelText("CNPJ"), CNPJ);
  await user.click(screen.getByRole("button", { name: "Consultar CNPJ" }));
  return { user, fetchMock };
}

async function openDetails(responses: Parameters<typeof mockFetch>[0] = {}) {
  const opened = await lookUpCnpj({ [LOOKUP]: { body: INSTITUTION_PREVIEW }, ...responses });
  await opened.user.click(
    await screen.findByRole("button", { name: "Continuar para os detalhes" }),
  );
  return opened;
}

describe("InstitutionForm", () => {
  it("previews official CNPJ data and submits the completed institution", async () => {
    const { user, fetchMock } = await lookUpCnpj({
      [LOOKUP]: { body: INSTITUTION_PREVIEW },
      "POST /api/institutions": { status: 201, body: INSTITUTION },
      "GET /api/institutions/me": { body: [INSTITUTION] },
    });

    expect(await screen.findByText(INSTITUTION_PREVIEW.legal_name)).toBeTruthy();
    expect(screen.getByText("Associação")).toBeTruthy();
    expect(screen.getByText("Organização sem fins lucrativos")).toBeTruthy();
    expect(screen.getByText(INSTITUTION_PREVIEW.reasons[2])).toBeTruthy();

    await user.click(screen.getByRole("button", { name: "Continuar para os detalhes" }));
    const tradeName = screen.getByLabelText("Nome fantasia");
    await user.clear(tradeName);
    await user.type(tradeName, "AACD");
    const description = screen.getByRole("textbox", {
      name: "Descrição",
      description: "Conte um pouco sobre o trabalho realizado.",
    });
    await user.type(description, "Reabilitação e inclusão.");
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

  it("locks the CNPJ while the lookup runs", async () => {
    mockFetch(MANAGER_SESSION);
    const user = renderApp("/instituicoes/nova");
    await user.type(await screen.findByLabelText("CNPJ"), CNPJ);
    vi.stubGlobal(
      "fetch",
      vi.fn(() => new Promise<Response>(() => undefined)),
    );

    await user.click(screen.getByRole("button", { name: "Consultar CNPJ" }));

    expect(field("CNPJ").readOnly).toBe(true);
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
    await lookUpCnpj({ [LOOKUP]: { status, body: { detail } } });

    expect((await screen.findByRole("alert")).textContent).toBe(detail);
    expect(screen.getByLabelText("CNPJ")).toBeTruthy();
  });

  it.each([
    ["UF", "S"],
    ["E-mail de contato (opcional)", "contato@exemplo"],
    ["Site (opcional)", "ftp://exemplo.org"],
  ])("keeps the form when %s is %s, which the API refuses", async (label, text) => {
    const { user, fetchMock } = await openDetails();

    await user.type(screen.getByLabelText("Descrição"), "Reabilitação e inclusão.");
    await user.clear(screen.getByLabelText(label));
    await user.type(screen.getByLabelText(label), text);
    await user.click(screen.getByRole("button", { name: "Cadastrar instituição" }));

    expect(requestsMade(fetchMock)).not.toContain("POST /api/institutions");
  });

  it("shows why the registration was refused", async () => {
    const detail = "Já existe uma instituição cadastrada com o CNPJ 60979457000111.";
    const { user } = await openDetails({
      "POST /api/institutions": { status: 409, body: { detail } },
    });

    await user.type(screen.getByLabelText("Descrição"), "Reabilitação e inclusão.");
    await user.click(screen.getByRole("button", { name: "Cadastrar instituição" }));

    expect((await screen.findByRole("alert")).textContent).toBe(detail);
  });
});
