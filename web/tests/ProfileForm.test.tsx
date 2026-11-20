import { screen } from "@testing-library/react";
import type { UserEvent } from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import {
  bodySent,
  DONOR,
  field,
  MANAGER,
  mockFetch,
  openProfile,
  requestsMade,
  UNAUTHORIZED,
} from "./helpers";

const SAVE = "PATCH /api/profiles/me";
const SAVED = { [SAVE]: { body: DONOR } };

async function retype(user: UserEvent, label: string, text: string) {
  await user.clear(field(label));
  await user.type(field(label), text);
}

function save(user: UserEvent) {
  return user.click(screen.getByRole("button", { name: "Salvar" }));
}

describe("ProfileForm", () => {
  it("fills the form with the saved data, formatting the phone and the CEP", async () => {
    await openProfile(DONOR);

    expect(field("Nome completo").value).toBe("Maria Silva");
    expect(field("DDD").value).toBe("11");
    expect(field("Telefone").value).toBe("99999-0000");
    expect(field("CEP").value).toBe("01310-200");
    expect(field("Animais").checked).toBe(true);
    expect(field("Idosos").checked).toBe(false);
  });

  it("saves what a donor changed and confirms it", async () => {
    const saved = { ...DONOR, name: "Maria Souza" };
    const { user, fetchMock } = await openProfile(DONOR, { [SAVE]: { body: saved } });

    await retype(user, "Nome completo", "Maria Souza");
    await retype(user, "DDD", "21");
    await retype(user, "Telefone", "20000000");
    await user.click(field("Saúde"));
    await user.click(field("Idosos"));
    await retype(user, "CEP", "69945000{Enter}");

    expect((await screen.findByRole("status")).textContent).toBe("Perfil atualizado.");
    expect(screen.getByText("Maria Souza")).toBeTruthy();
    expect(bodySent(fetchMock, SAVE)).toEqual({
      name: "Maria Souza",
      phone: "2120000000",
      postal_code: "69945-000",
      preferred_causes: ["animals", "elderly"],
    });
  });

  it("lets a manager edit only the name and the phone", async () => {
    const { user, fetchMock } = await openProfile(MANAGER, { [SAVE]: { body: MANAGER } });

    expect(screen.queryByLabelText("CEP")).toBeNull();
    expect(screen.queryByRole("checkbox")).toBeNull();
    await retype(user, "Nome completo", "Ana Lima");
    await save(user);

    await screen.findByRole("status");
    expect(bodySent(fetchMock, SAVE)).toEqual({ name: "Ana Lima", phone: null });
  });

  it("requires the phone only after one was saved", async () => {
    const { user } = await openProfile({ ...DONOR, phone: null }, SAVED);

    expect(field("DDD").required).toBe(false);
    expect(field("Telefone (opcional)").required).toBe(false);
    await user.type(field("DDD"), "11");
    await user.type(field("Telefone (opcional)"), "999990000");
    await save(user);

    await screen.findByRole("status");
    expect(field("DDD").required).toBe(true);
    expect(field("Telefone").required).toBe(true);
  });

  it("hides the confirmation when a field changes after the save", async () => {
    const { user } = await openProfile(DONOR, SAVED);
    await save(user);
    await screen.findByRole("status");

    await user.click(field("Idosos"));

    expect(screen.queryByRole("status")).toBeNull();
  });

  it("replaces the confirmation with the refusal reason and keeps what was typed", async () => {
    const detail = "O telefone informado é inválido.";
    const { user } = await openProfile(DONOR, SAVED);
    await retype(user, "Telefone", "9999000");
    await save(user);
    await screen.findByRole("status");
    mockFetch({ [SAVE]: { status: 422, body: { detail } } });

    await save(user);

    expect((await screen.findByRole("alert")).textContent).toBe(detail);
    expect(screen.queryByRole("status")).toBeNull();
    expect(field("Telefone").value).toBe("9999000");
  });

  it("does not send the form without a name", async () => {
    const { user, fetchMock } = await openProfile(DONOR);

    await user.clear(field("Nome completo"));
    await save(user);

    expect(requestsMade(fetchMock)).not.toContain(SAVE);
  });

  it("goes back to the login when the session has expired", async () => {
    const { user } = await openProfile(DONOR, { [SAVE]: UNAUTHORIZED });

    await save(user);

    expect(await screen.findByRole("link", { name: "Entrar com o Google" })).toBeTruthy();
  });

  it("goes back to the home page on cancel", async () => {
    const { user } = await openProfile(DONOR);

    await user.click(screen.getByRole("link", { name: "Cancelar" }));

    expect(await screen.findByRole("heading", { name: "Olá, Maria Silva" })).toBeTruthy();
  });
});
