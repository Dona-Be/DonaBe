import { screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { mockFetch, NEWCOMER, NEWCOMER_SESSION, renderApp, requestsMade } from "./helpers";

const MANAGER = { ...NEWCOMER, role: "manager" };

function radio(name: string): HTMLInputElement {
  return screen.getByRole("radio", { name });
}

describe("ProfileSetup", () => {
  it("asks a user without a role to choose one, with donor preselected", async () => {
    mockFetch(NEWCOMER_SESSION);

    renderApp("/");

    expect(await screen.findByRole("heading", { name: "Perfil" })).toBeTruthy();
    expect(radio("Quero doar").checked).toBe(true);
    expect(radio("Represento uma instituição").checked).toBe(false);
    expect(screen.getByText("Esta escolha não pode ser alterada depois.")).toBeTruthy();
  });

  it("creates the manager and opens the dashboard", async () => {
    const fetchMock = mockFetch({
      ...NEWCOMER_SESSION,
      "POST /api/profiles/manager": { status: 201, body: MANAGER },
    });
    const user = renderApp("/");

    await user.click(await screen.findByRole("radio", { name: "Represento uma instituição" }));
    await user.click(screen.getByRole("button", { name: "Continuar" }));

    expect(await screen.findByRole("heading", { name: "Olá, Maria Silva" })).toBeTruthy();
    expect(screen.getByText("Gestor de instituição")).toBeTruthy();
    expect(requestsMade(fetchMock)).toContain("POST /api/profiles/manager");
  });

  it("explains when the user already has a role and allows a retry", async () => {
    mockFetch({
      ...NEWCOMER_SESSION,
      "POST /api/profiles/manager": {
        status: 409,
        body: { detail: "Você já escolheu o seu papel." },
      },
    });
    const user = renderApp("/");

    await user.click(await screen.findByRole("radio", { name: "Represento uma instituição" }));
    await user.click(screen.getByRole("button", { name: "Continuar" }));

    expect((await screen.findByRole("alert")).textContent).toBe("Você já escolheu o seu papel.");
    expect(screen.getByRole("button", { name: "Continuar" }).hasAttribute("disabled")).toBe(false);
  });

  it("forgets a failure after opening the donor form and going back", async () => {
    mockFetch({ ...NEWCOMER_SESSION, "POST /api/profiles/manager": { status: 500 } });
    const user = renderApp("/");

    await user.click(await screen.findByRole("radio", { name: "Represento uma instituição" }));
    await user.click(screen.getByRole("button", { name: "Continuar" }));
    await screen.findByRole("alert");
    await user.click(screen.getByRole("radio", { name: "Quero doar" }));
    await user.click(screen.getByRole("button", { name: "Continuar" }));
    await user.click(screen.getByRole("button", { name: "Voltar" }));

    expect(screen.getByRole("heading", { name: "Perfil" })).toBeTruthy();
    expect(screen.queryByRole("alert")).toBeNull();
  });

  it("goes back to the login when the pending signup has expired", async () => {
    mockFetch({ ...NEWCOMER_SESSION, "POST /api/profiles/manager": { status: 401 } });
    const user = renderApp("/");

    await user.click(await screen.findByRole("radio", { name: "Represento uma instituição" }));
    await user.click(screen.getByRole("button", { name: "Continuar" }));

    expect(await screen.findByRole("link", { name: "Entrar com o Google" })).toBeTruthy();
  });

  it("logs out from the role choice and goes to the login page", async () => {
    const fetchMock = mockFetch({ ...NEWCOMER_SESSION, "POST /api/auth/logout": { status: 204 } });
    const user = renderApp("/");

    await user.click(await screen.findByRole("button", { name: "Sair" }));

    expect(await screen.findByRole("link", { name: "Entrar com o Google" })).toBeTruthy();
    expect(requestsMade(fetchMock)).toContain("POST /api/auth/logout");
  });
});
