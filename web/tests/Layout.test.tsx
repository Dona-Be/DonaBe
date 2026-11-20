import { act, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { mockFetch, renderApp, requestsMade, USER } from "./helpers";

const SESSION = { "GET /api/profiles/me": { body: USER } };
const LOGOUT = "POST /api/auth/logout";

describe("Layout", () => {
  it("links the home page and the profile", async () => {
    mockFetch(SESSION);
    const user = renderApp("/");

    await user.click(await screen.findByRole("link", { name: "Meu perfil" }));

    expect(screen.getByRole("heading", { name: "Meu perfil" })).toBeTruthy();
    await user.click(screen.getByRole("link", { name: "Início" }));

    expect(screen.getByRole("heading", { name: "Olá, Maria Silva" })).toBeTruthy();
  });

  it("logs out and goes to the login page", async () => {
    const fetchMock = mockFetch({ ...SESSION, [LOGOUT]: { status: 204 } });
    const user = renderApp("/");

    await user.click(await screen.findByRole("button", { name: "Sair" }));

    expect(await screen.findByRole("link", { name: "Entrar com o Google" })).toBeTruthy();
    expect(requestsMade(fetchMock)).toContain(LOGOUT);
  });

  it("warns when it cannot log out and keeps the page open", async () => {
    mockFetch({ ...SESSION, [LOGOUT]: { status: 500, body: { detail: "Falha interna." } } });
    const user = renderApp("/perfil");

    await user.click(await screen.findByRole("button", { name: "Sair" }));

    expect((await screen.findByRole("alert")).textContent).toBe("Falha interna.");
    expect(screen.getByRole("heading", { name: "Meu perfil" })).toBeTruthy();
  });

  it.each(["Salvar", "Sair"])("disables %s while its request is open", async (name) => {
    const fetchMock = mockFetch(SESSION);
    const user = renderApp("/perfil");
    const button = await screen.findByRole("button", { name });
    fetchMock.mockReturnValue(new Promise<Response>(() => undefined));

    await user.click(button);

    expect(button.hasAttribute("disabled")).toBe(true);
  });

  it("stays logged out when a save answers after the logout", async () => {
    const fetchMock = mockFetch({ ...SESSION, [LOGOUT]: { status: 204 } });
    const user = renderApp("/perfil");
    const save = await screen.findByRole("button", { name: "Salvar" });
    let answer: (response: Response) => void = () => undefined;
    fetchMock.mockReturnValueOnce(new Promise((resolve) => (answer = resolve)));

    await user.click(save);
    await user.click(screen.getByRole("button", { name: "Sair" }));
    await screen.findByRole("link", { name: "Entrar com o Google" });
    await act(async () => {
      answer(Response.json(USER));
      await new Promise((resolve) => setTimeout(resolve));
    });

    expect(screen.queryByRole("heading", { name: "Olá, Maria Silva" })).toBeNull();
  });
});
