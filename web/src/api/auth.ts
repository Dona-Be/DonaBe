import { API_PREFIX, post } from "./client";

export const GOOGLE_LOGIN_URL = `${API_PREFIX}/auth/login/google`;

export function logout(): Promise<undefined> {
  return post<undefined>("/auth/logout");
}
