import type { Cause } from "../causes";
import { FriendlyError } from "../errors";
import type { Profile } from "../types/user";
import { get, patch, post } from "./client";

const UNAUTHORIZED = 401;

export interface NewDonor {
  postal_code: string;
  phone: string | null;
  preferred_causes: Cause[];
}

export interface ProfileChanges extends Partial<NewDonor> {
  name: string;
}

export function readMyProfile(): Promise<Profile> {
  return get<Profile>("/profiles/me");
}

// A 401 means the signup or the session expired, so the login page takes over.
async function nullIfExpired(request: Promise<Profile>): Promise<Profile | null> {
  try {
    return await request;
  } catch (error) {
    if (error instanceof FriendlyError && error.httpStatus === UNAUTHORIZED) return null;
    throw error;
  }
}

export function createDonor(donor: NewDonor): Promise<Profile | null> {
  return nullIfExpired(post<Profile>("/profiles/donor", donor));
}

export function createManager(): Promise<Profile | null> {
  return nullIfExpired(post<Profile>("/profiles/manager"));
}

export function updateMyProfile(changes: ProfileChanges): Promise<Profile | null> {
  return nullIfExpired(patch<Profile>("/profiles/me", changes));
}
