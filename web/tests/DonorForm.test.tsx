import { screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import {
  bodySent,
  mockFetch,
  NEWCOMER_SESSION,
  renderApp,
  requestsMade,
  UNAUTHORIZED,
  USER,
} from "./helpers";

const SIGNUP = "POST /api/profiles/donor";

async function openDonorForm(responses: Parameters<typeof mockFetch>[0] = {}) {
  const fetchMock = mockFetch({ ...NEWCOMER_SESSION, ...responses });
  const user = renderApp("/");
  await user.click(await screen.findByRole("button", { name: "Continuar" }));
  return { user, fetchMock };
}

describe("DonorForm", () => {
  it("opens after choosing to donate and goes back to the role choice", async () => {
    const { user } = await openDonorForm();

    expect(screen.getByRole("heading", { name: "Local e Contato" })).toBeTruthy();
    await user.click(screen.getByRole("button", { name: "Voltar" }));

    expect(screen.getByRole("heading", { name: "Perfil" })).toBeTruthy();
  });

  it("sends the CEP, the phone and the chosen causes, then opens the dashboard", async () => {
    const { user, fetchMock } = await openDonorForm({ [SIGNUP]: { status: 201, body: USER } });

    await user.type(screen.getByLabelText("CEP"), "01310-200");
    await user.type(screen.getByLabelText("Telefone (opcional)"), "(11) 99999-0000");
    await user.click(screen.getByRole("checkbox", { name: "Animais" }));
    await user.click(screen.getByRole("checkbox", { name: "Saúde" }));
    await user.click(screen.getByRole("button", { name: "Concluir cadastro" }));

    expect(await screen.findByRole("heading", { name: "Olá, Maria Silva" })).toBeTruthy();
    expect(bodySent(fetchMock, SIGNUP)).toEqual({
      postal_code: "01310-200",
      phone: "(11) 99999-0000",
      preferred_causes: ["animals", "health"],
    });
  });

  it("sends no phone when it is left empty and drops a cause that was unchecked", async () => {
    const { user, fetchMock } = await openDonorForm({ [SIGNUP]: { status: 201, body: USER } });

    await user.type(screen.getByLabelText("CEP"), "01310200");
    await user.click(screen.getByRole("checkbox", { name: "Idosos" }));
    await user.click(screen.getByRole("checkbox", { name: "Educação" }));
    await user.click(screen.getByRole("checkbox", { name: "Idosos" }));
    await user.click(screen.getByRole("button", { name: "Concluir cadastro" }));

    await screen.findByRole("heading", { name: "Olá, Maria Silva" });
    expect(bodySent(fetchMock, SIGNUP)).toEqual({
      postal_code: "01310200",
      phone: null,
      preferred_causes: ["education"],
    });
  });

  it("does not send the form without a CEP", async () => {
    const { user, fetchMock } = await openDonorForm();

    await user.click(screen.getByRole("button", { name: "Concluir cadastro" }));

    expect(requestsMade(fetchMock)).not.toContain(SIGNUP);
  });

  it("goes back to the login when the pending signup has expired", async () => {
    const { user } = await openDonorForm({ [SIGNUP]: UNAUTHORIZED });

    await user.type(screen.getByLabelText("CEP"), "01310200");
    await user.click(screen.getByRole("button", { name: "Concluir cadastro" }));

    expect(await screen.findByRole("link", { name: "Entrar com o Google" })).toBeTruthy();
  });

  it("shows the reason of a refusal and keeps what was typed", async () => {
    const detail = "O CEP 69945000 não tem uma localização conhecida. Informe um CEP próximo.";
    const { user } = await openDonorForm({ [SIGNUP]: { status: 422, body: { detail } } });

    await user.type(screen.getByLabelText("CEP"), "69945-000");
    await user.click(screen.getByRole("button", { name: "Concluir cadastro" }));

    expect((await screen.findByRole("alert")).textContent).toBe(detail);
    expect(screen.getByLabelText<HTMLInputElement>("CEP").value).toBe("69945-000");
    expect(screen.getByRole("button", { name: "Concluir cadastro" }).hasAttribute("disabled")).toBe(
      false,
    );
  });
});
