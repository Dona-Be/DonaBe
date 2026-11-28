import { screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { DONOR, mockFetch, renderApp, requestsMade } from "./helpers";
import { CLOSED, FULFILLED, NEED, PAGE, card, filter, openNeeds } from "./needs";

describe("InstitutionNeeds", () => {
  it("shows a clear empty state and cancels a new need", async () => {
    const { user } = openNeeds([]);

    expect(
      await screen.findByRole("heading", { level: 1, name: "Necessidades – Aacd Ibirapuera" }),
    ).toBeTruthy();
    expect(
      screen.getByRole("heading", { name: "Nenhuma necessidade publicada ainda" }),
    ).toBeTruthy();
    expect(screen.queryByRole("group", { name: "Filtrar por status" })).toBeNull();
    await user.click(screen.getByRole("button", { name: "Nova necessidade" }));
    expect(screen.queryByRole("heading", { name: /^Nenhuma necessidade/ })).toBeNull();
    await user.click(screen.getByRole("button", { name: "Cancelar" }));
    expect(screen.queryByRole("form", { name: "Nova necessidade" })).toBeNull();
    expect(screen.getByRole("heading", { name: /^Nenhuma necessidade/ })).toBeTruthy();
  });

  it("lists the needs by status", async () => {
    const { user } = openNeeds([NEED, FULFILLED, CLOSED]);

    expect(await screen.findByRole("article", { name: "Cobertores" })).toBeTruthy();
    expect(screen.queryByRole("heading", { name: /^Nenhuma necessidade/ })).toBeNull();
    expect(filter(/^Abertas/).textContent).toBe("Abertas 1");
    expect(filter(/^Atendidas/).textContent).toBe("Atendidas 1");
    expect(filter(/^Encerradas/).textContent).toBe("Encerradas 1");
    expect(screen.queryByRole("article", { name: "Fraldas" })).toBeNull();

    await user.click(filter(/^Atendidas/));
    const fulfilled = card("Fraldas");
    expect(fulfilled.getByText("Atendida em 20/11/2026")).toBeTruthy();
    expect(fulfilled.queryByText(/^Quantidade/)).toBeNull();
    expect(fulfilled.queryByRole("button")).toBeNull();
    expect(screen.queryByRole("article", { name: "Cobertores" })).toBeNull();

    await user.click(filter(/^Encerradas/));
    expect(filter(/^Encerradas/).getAttribute("aria-pressed")).toBe("true");
    expect(card("Leite em pó").getByText("Encerrada em 20/11/2026")).toBeTruthy();
  });

  it("says when there is nothing in a status", async () => {
    const { user } = openNeeds([FULFILLED]);

    expect(await screen.findByText("Nenhuma necessidade aberta no momento.")).toBeTruthy();
    await user.click(filter(/^Encerradas/));
    expect(screen.getByText("Nenhuma necessidade encerrada.")).toBeTruthy();
  });

  it("is reachable from the manager's institutions", async () => {
    const { user } = openNeeds([NEED], {}, "/instituicoes");

    await user.click(await screen.findByRole("link", { name: "Necessidades" }));

    expect(await screen.findByRole("article", { name: "Cobertores" })).toBeTruthy();
  });

  it("does not open the needs of another manager's institution", async () => {
    const { fetchMock } = openNeeds([], {}, "/instituicoes/2/necessidades");

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
