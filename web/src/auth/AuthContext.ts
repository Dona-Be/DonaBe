import { createContext } from "react";
import type { Profile, Role } from "../types/user";

export interface AuthValue {
  user: Profile | null;
  role: Role | null;
  loading: boolean;
  setUser: (user: Profile | null) => void;
}

export const AuthContext = createContext<AuthValue | null>(null);
