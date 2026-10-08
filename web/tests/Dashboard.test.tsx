import { screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { mockFetch, mockNetworkFailure, renderApp, requestsMade, UNAUTHORIZED, USER, VISITOR } from "./helpers";

describe("Dashboard", () => {
  it("shows the name, e-mail and role of the current user", async () => {
    mockFetch({ "GET /api/auth/me": { body: USER } });

    renderApp("/");

    expect(await screen.findByRole("heading", { name: "Olá, Maria Silva" })).toBeTruthy();
    expect(screen.getByText("maria@exemplo.com")).toBeTruthy();
    expect(screen.getByText("Doador")).toBeTruthy();
    expect(screen.getByText("Este é o seu painel. As funcionalidades vão aparecer aqui.")).toBeTruthy();
  });

  it("logs out and goes to the login page", async () => {
    const fetchMock = mockFetch({
      "GET /api/auth/me": { body: USER },
      "POST /api/auth/logout": { status: 204 },
      "GET /api/auth/pending-signup": UNAUTHORIZED,
    });
    const user = renderApp("/");

    await user.click(await screen.findByRole("button", { name: "Sair" }));

    expect(await screen.findByRole("link", { name: "Entrar com Google" })).toBeTruthy();
    expect(requestsMade(fetchMock)).toContain("POST /api/auth/logout");
  });

  it("warns when it cannot log out", async () => {
    mockFetch({
      "GET /api/auth/me": { body: USER },
      "POST /api/auth/logout": { status: 500, body: { detail: "Falha interna." } },
    });
    const user = renderApp("/");

    await user.click(await screen.findByRole("button", { name: "Sair" }));

    expect((await screen.findByRole("alert")).textContent).toBe("Falha interna.");
    expect(screen.getByRole("heading", { name: "Olá, Maria Silva" })).toBeTruthy();
  });

  it("sends a visitor to the login page", async () => {
    mockFetch(VISITOR);

    renderApp("/");

    expect(await screen.findByRole("link", { name: "Entrar com Google" })).toBeTruthy();
  });

  it("treats a failed session check as a visitor", async () => {
    mockNetworkFailure();

    renderApp("/");

    expect(await screen.findByRole("link", { name: "Entrar com Google" })).toBeTruthy();
  });

  it("sends unknown routes to the dashboard", async () => {
    mockFetch({ "GET /api/auth/me": { body: USER } });

    renderApp("/unknown");

    expect(await screen.findByRole("heading", { name: "Olá, Maria Silva" })).toBeTruthy();
  });
});
