import { createContext, type Dispatch, type SetStateAction } from "react";
import type { Profile, Role } from "../types/user";

export interface AuthValue {
  user: Profile | null;
  role: Role | null;
  loading: boolean;
  setUser: Dispatch<SetStateAction<Profile | null>>;
}

export const AuthContext = createContext<AuthValue | null>(null);
