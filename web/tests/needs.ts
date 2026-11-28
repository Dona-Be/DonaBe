import { screen, within } from "@testing-library/react";
import { INSTITUTION, MANAGER_SESSION, mockFetch, renderApp } from "./helpers";

export const PAGE = "/instituicoes/1/necessidades";
export const CLOSED_AT = "2026-11-20T12:00:00";

export const NEED = {
  id: 7,
  title: "Cobertores",
  description: "Cobertores de casal para o inverno.",
  quantity: "20 unidades",
  status: "open",
  closed_at: null,
};
export const FULFILLED = {
  ...NEED,
  id: 8,
  title: "Fraldas",
  quantity: null,
  status: "fulfilled",
  closed_at: CLOSED_AT,
};
export const CLOSED = {
  ...NEED,
  id: 9,
  title: "Leite em pó",
  status: "closed",
  closed_at: CLOSED_AT,
};

type Responses = Parameters<typeof mockFetch>[0];

export function openNeeds(needs: unknown[], responses: Responses = {}, path = PAGE) {
  const fetchMock = mockFetch({
    ...MANAGER_SESSION,
    "GET /api/institutions/me": { body: [INSTITUTION] },
    "GET /api/institutions/1/needs": { body: needs },
    ...responses,
  });
  return { fetchMock, user: renderApp(path) };
}

export function card(title: string) {
  return within(screen.getByRole("article", { name: title }));
}

export async function loadedCard(title: string) {
  return within(await screen.findByRole("article", { name: title }));
}

export function filter(name: RegExp) {
  const group = within(screen.getByRole("group", { name: "Filtrar por status" }));
  return group.getByRole("button", { name });
}
