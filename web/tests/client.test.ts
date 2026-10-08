import { describe, expect, it } from "vitest";
import { get, post } from "../src/api/client";
import { FriendlyError } from "../src/errors";
import { mockFetch, mockNetworkFailure } from "./helpers";

describe("get", () => {
  it("sends the session cookie and returns the JSON body", async () => {
    const fetchMock = mockFetch({ "GET /api/resource": { body: { name: "DonaBe" } } });

    await expect(get("/resource")).resolves.toEqual({ name: "DonaBe" });
    expect(fetchMock.mock.calls[0][1]?.credentials).toBe("include");
  });

  it("uses a string detail as the error message and keeps the HTTP status", async () => {
    const detail = "Já existe um usuário cadastrado com o e-mail maria@exemplo.com.";
    mockFetch({ "GET /api/resource": { status: 409, body: { detail } } });

    await expect(get("/resource")).rejects.toBeInstanceOf(FriendlyError);
    await expect(get("/resource")).rejects.toMatchObject({ message: detail, httpStatus: 409 });
  });

  it("replaces a validation detail list with a friendly message", async () => {
    mockFetch({ "GET /api/resource": { status: 422, body: { detail: [{ loc: ["body", "role"], msg: "invalid" }] } } });

    await expect(get("/resource")).rejects.toMatchObject({
      message: "Alguns dados enviados são inválidos. Revise e tente novamente.",
    });
  });

  it("uses a default message when the error body has no detail", async () => {
    mockFetch({ "GET /api/resource": { status: 500 } });

    await expect(get("/resource")).rejects.toMatchObject({
      message: "O servidor não conseguiu concluir a operação. Tente novamente.",
    });
  });

  it("explains when the server cannot be reached", async () => {
    mockNetworkFailure();

    await expect(get("/resource")).rejects.toMatchObject({
      message: "Não foi possível falar com o servidor. Verifique sua conexão.",
    });
  });
});

describe("post", () => {
  it("sends the body as JSON", async () => {
    const fetchMock = mockFetch({ "POST /api/resource": { status: 201, body: { id: 7 } } });

    await expect(post("/resource", { role: "donor" })).resolves.toEqual({ id: 7 });
    expect(fetchMock.mock.calls[0][1]?.body).toBe('{"role":"donor"}');
  });

  it("accepts an empty 204 response", async () => {
    mockFetch({ "POST /api/resource": { status: 204 } });

    await expect(post("/resource")).resolves.toBeUndefined();
  });
});
