import { screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { bodySent, mockFetch, mockNetworkFailure, renderApp, UNAUTHORIZED, USER, VISITOR } from "./helpers";

const PENDING_SIGNUP = { email: "maria@exemplo.com", name: "Maria Silva", picture_url: null };

describe("Login", () => {
  it("offers the Google login to a visitor", async () => {
    mockFetch(VISITOR);

    renderApp("/login");

    const link = await screen.findByRole("link", { name: "Entrar com Google" });
    expect(link.getAttribute("href")).toBe("/api/auth/login/google");
    expect(screen.queryByRole("alert")).toBeNull();
  });

  it("explains when the Google login failed", async () => {
    mockFetch(VISITOR);

    renderApp("/login?error=login_failed");

    expect((await screen.findByRole("alert")).textContent).toBe("Não foi possível entrar com o Google. Tente novamente.");
  });

  it("ignores unknown values of the error parameter", async () => {
    mockFetch(VISITOR);

    renderApp("/login?error=something_else");

    await screen.findByRole("link", { name: "Entrar com Google" });
    expect(screen.queryByRole("alert")).toBeNull();
  });

  it("still offers the Google login when the pending signup cannot be checked", async () => {
    mockNetworkFailure();

    renderApp("/login");

    await screen.findByRole("link", { name: "Entrar com Google" });
    expect(screen.getByRole("alert").textContent).toBe("Não foi possível falar com o servidor. Verifique sua conexão.");
  });

  it("shows the role choice when there is a pending signup and goes to the dashboard after choosing", async () => {
    const fetchMock = mockFetch({
      "GET /api/auth/me": UNAUTHORIZED,
      "GET /api/auth/pending-signup": { body: PENDING_SIGNUP },
      "POST /api/auth/signup": { status: 201, body: { ...USER, role: "manager" } },
    });
    const user = renderApp("/login");

    expect(await screen.findByRole("heading", { name: "Boas-vindas ao DonaBe" })).toBeTruthy();
    expect(screen.getByText("maria@exemplo.com")).toBeTruthy();
    expect(screen.getByText(/Esta escolha não pode ser alterada depois/)).toBeTruthy();
    await user.click(screen.getByRole("button", { name: "Represento uma instituição" }));

    expect(await screen.findByRole("heading", { name: "Olá, Maria Silva" })).toBeTruthy();
    expect(screen.getByText("Gestor de instituição")).toBeTruthy();
    expect(bodySent(fetchMock, "POST /api/auth/signup")).toEqual({ role: "manager" });
  });

  it("shows the signup failure and lets the visitor try again", async () => {
    mockFetch({
      "GET /api/auth/me": UNAUTHORIZED,
      "GET /api/auth/pending-signup": { body: PENDING_SIGNUP },
      "POST /api/auth/signup": {
        status: 409,
        body: { detail: "Já existe um usuário cadastrado com o e-mail maria@exemplo.com." },
      },
    });
    const user = renderApp("/login");

    await user.click(await screen.findByRole("button", { name: "Sou doador" }));

    expect((await screen.findByRole("alert")).textContent).toBe(
      "Já existe um usuário cadastrado com o e-mail maria@exemplo.com.",
    );
    expect(screen.getByRole("button", { name: "Sou doador" }).hasAttribute("disabled")).toBe(false);
  });

  it("sends a logged-in user to the dashboard", async () => {
    mockFetch({ "GET /api/auth/me": { body: USER } });

    renderApp("/login");

    expect(await screen.findByRole("heading", { name: "Olá, Maria Silva" })).toBeTruthy();
  });
});
