import { screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { mockFetch, NEWCOMER_SESSION, renderApp, USER, VISITOR } from "./helpers";

describe("Login", () => {
  it("offers the Google login to a visitor", async () => {
    mockFetch(VISITOR);

    renderApp("/login");

    const link = await screen.findByRole("link", { name: "Entrar com o Google" });
    expect(link.getAttribute("href")).toBe("/api/auth/login/google");
    expect(screen.queryByRole("alert")).toBeNull();
  });

  it("explains when the Google login failed", async () => {
    mockFetch(VISITOR);

    renderApp("/login?error=login_failed");

    expect((await screen.findByRole("alert")).textContent).toBe(
      "Não foi possível entrar com o Google. Tente novamente.",
    );
  });

  it("ignores unknown values of the error parameter", async () => {
    mockFetch(VISITOR);

    renderApp("/login?error=something_else");

    await screen.findByRole("link", { name: "Entrar com o Google" });
    expect(screen.queryByRole("alert")).toBeNull();
  });

  it("sends a logged-in user to the dashboard", async () => {
    mockFetch({ "GET /api/profiles/me": { body: USER } });

    renderApp("/login");

    expect(await screen.findByRole("heading", { name: "Olá, Maria Silva" })).toBeTruthy();
  });

  it("sends a user without a role to the role choice", async () => {
    mockFetch(NEWCOMER_SESSION);

    renderApp("/login");

    expect(await screen.findByRole("heading", { name: "Perfil" })).toBeTruthy();
  });
});
