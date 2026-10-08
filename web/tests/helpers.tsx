import { render } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router";
import { vi } from "vitest";
import { App } from "../src/App";
import { AuthProvider } from "../src/auth/AuthProvider";
import type { PublicUser } from "../src/types/user";

interface FakeResponse {
  status?: number;
  body?: unknown;
}

export const USER: PublicUser = {
  id: 1,
  email: "maria@exemplo.com",
  name: "Maria Silva",
  picture_url: null,
  role: "donor",
};

export const UNAUTHORIZED: FakeResponse = { status: 401, body: { detail: "Você precisa entrar para continuar." } };

export const VISITOR = { "GET /api/auth/me": UNAUTHORIZED, "GET /api/auth/pending-signup": UNAUTHORIZED };

function requestKey(input: RequestInfo | URL, options?: RequestInit): string {
  const url = input instanceof Request ? input.url : input.toString();
  return `${options?.method ?? "GET"} ${url}`;
}

function toResponse({ status = 200, body }: FakeResponse): Response {
  if (body === undefined) return new Response(null, { status });
  return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
}

export function mockFetch(responses: Record<string, FakeResponse>) {
  const fetchMock = vi.fn(async (input: RequestInfo | URL, options?: RequestInit): Promise<Response> => {
    const response = responses[requestKey(input, options)];
    if (!response) throw new Error(`Unexpected request: ${requestKey(input, options)}`);
    return toResponse(response);
  });
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
