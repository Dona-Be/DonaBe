import { createContext } from "react";
import type { PublicUser } from "../types/user";

export interface AuthValue {
  user: PublicUser | null;
  loading: boolean;
  setUser: (user: PublicUser | null) => void;
}

export const AuthContext = createContext<AuthValue | null>(null);
