import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router";
import { vi } from "vitest";
import { App } from "../src/App";
import { AuthProvider } from "../src/auth/AuthProvider";
import type { Profile } from "../src/types/user";

interface FakeResponse {
  status?: number;
  body?: unknown;
}

export const USER: Profile = {
  email: "maria@exemplo.com",
  name: "Maria Silva",
  picture_url: null,
  phone: null,
  role: "donor",
  postal_code: "01310200",
  preferred_causes: ["animals", "health"],
};

export const NEWCOMER: Profile = { ...USER, role: null, postal_code: null, preferred_causes: null };

export const MANAGER: Profile = { ...NEWCOMER, role: "manager" };

export const DONOR: Profile = {
  ...USER,
  picture_url: "https://lh3.googleusercontent.com/a/maria",
  phone: "11999990000",
};

export const UNAUTHORIZED: FakeResponse = {
  status: 401,
  body: { detail: "Nenhum cadastro pendente. Entre com o Google novamente." },
};

export const VISITOR = { "GET /api/profiles/me": UNAUTHORIZED };

export const NEWCOMER_SESSION = { "GET /api/profiles/me": { body: NEWCOMER } };

export const MANAGER_SESSION = { "GET /api/profiles/me": { body: MANAGER } };

export const INSTITUTION_PREVIEW = {
  type: "association",
  cnpj: "60979457000111",
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

export const INSTITUTION = {
  ...INSTITUTION_PREVIEW,
  id: 1,
  description: "Reabilitação de crianças com deficiência.",
  causes: ["health", "people_with_disabilities"],
  phone: "1120000000",
  contact_email: "contato@exemplo.org",
  website: "https://exemplo.org",
  instagram: "https://instagram.com/exemplo",
  facebook: "https://facebook.com/exemplo",
};

function requestKey(input: RequestInfo | URL, options?: RequestInit): string {
  const url = input instanceof Request ? input.url : input.toString();
  return `${options?.method ?? "GET"} ${url}`;
}

function toResponse({ status = 200, body }: FakeResponse): Response {
  if (body === undefined) return new Response(null, { status });
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

export function mockFetch(responses: Partial<Record<string, FakeResponse>>) {
  const fetchMock = vi.fn(
    async (input: RequestInfo | URL, options?: RequestInit): Promise<Response> => {
      const response = responses[requestKey(input, options)];
      if (!response) throw new Error(`Unexpected request: ${requestKey(input, options)}`);
      return toResponse(response);
    },
  );
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

export function requestsMade(fetchMock: ReturnType<typeof mockFetch>): string[] {
  return fetchMock.mock.calls.map(([input, options]) => requestKey(input, options));
}

export function bodySent(fetchMock: ReturnType<typeof mockFetch>, key: string): unknown {
  const call = fetchMock.mock.calls.find(([input, options]) => requestKey(input, options) === key);
  return typeof call?.[1]?.body === "string" ? JSON.parse(call[1].body) : undefined;
}

export function mockNetworkFailure() {
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => {
      throw new TypeError("Failed to fetch");
    }),
  );
}

export function renderApp(path: string) {
  render(
    <MemoryRouter initialEntries={[path]}>
      <AuthProvider>
        <App />
      </AuthProvider>
    </MemoryRouter>,
  );
  return userEvent.setup();
}

export function field(label: string): HTMLInputElement {
  return screen.getByLabelText(label);
}

export async function openProfile(
  profile: Profile,
  responses: Parameters<typeof mockFetch>[0] = {},
) {
  const fetchMock = mockFetch({ "GET /api/profiles/me": { body: profile }, ...responses });
  const user = renderApp("/perfil");
  await screen.findByRole("heading", { name: "Meu perfil" });
  return { user, fetchMock };
}
