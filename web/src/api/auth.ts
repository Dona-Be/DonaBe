import { FriendlyError } from "../errors";
import type { PendingSignup, PublicUser, Role } from "../types/user";
import { API_PREFIX, get, post } from "./client";

export const GOOGLE_LOGIN_URL = `${API_PREFIX}/auth/login/google`;

const UNAUTHORIZED = 401;

async function nullIfUnauthorized<T>(query: Promise<T>): Promise<T | null> {
  try {
    return await query;
  } catch (error) {
    if (error instanceof FriendlyError && error.httpStatus === UNAUTHORIZED) return null;
    throw error;
  }
}

export function readCurrentUser(): Promise<PublicUser | null> {
  return nullIfUnauthorized(get<PublicUser>("/auth/me"));
}

export function readPendingSignup(): Promise<PendingSignup | null> {
  return nullIfUnauthorized(get<PendingSignup>("/auth/pending-signup"));
}

export function signUp(role: Role): Promise<PublicUser> {
  return post<PublicUser>("/auth/signup", { role });
}

export function logout(): Promise<void> {
  return post<void>("/auth/logout");
}
