import { FriendlyError } from "../errors";

interface ErrorBody {
  detail?: unknown;
}

export const API_PREFIX = "/api";

const NO_CONTENT = 204;
const NO_CONNECTION_MESSAGE = "Não foi possível falar com o servidor. Verifique sua conexão.";
const INVALID_DATA_MESSAGE = "Alguns dados enviados são inválidos. Revise e tente novamente.";
const SERVER_FAILURE_MESSAGE = "O servidor não conseguiu concluir a operação. Tente novamente.";

async function errorFrom(response: Response): Promise<FriendlyError> {
  const body = (await response.json().catch(() => null)) as ErrorBody | null;
  if (typeof body?.detail === "string") return new FriendlyError(body.detail, response.status);
  if (Array.isArray(body?.detail)) return new FriendlyError(INVALID_DATA_MESSAGE, response.status);
  return new FriendlyError(SERVER_FAILURE_MESSAGE, response.status);
}

async function request<T>(path: string, options: RequestInit): Promise<T> {
  const response = await fetch(API_PREFIX + path, { ...options, credentials: "include" }).catch(
    () => {
      throw new FriendlyError(NO_CONNECTION_MESSAGE);
    },
  );

  if (!response.ok) throw await errorFrom(response);
  if (response.status === NO_CONTENT) return undefined as T;

  return response.json() as Promise<T>;
}

export function get<T>(path: string): Promise<T> {
  return request<T>(path, { method: "GET" });
}

export function post<T>(path: string, body?: unknown): Promise<T> {
  if (body === undefined) return request<T>(path, { method: "POST" });

  return request<T>(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}
