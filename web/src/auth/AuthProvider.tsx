import { useEffect, useState, type ReactNode } from "react";
import { readMyProfile } from "../api/profiles";
import type { Profile } from "../types/user";
import { AuthContext } from "./AuthContext";

export function AuthProvider({ children }: Readonly<{ children: ReactNode }>) {
  const [user, setUser] = useState<Profile | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    readMyProfile()
      .then(setUser)
      .catch(() => setUser(null))
      .finally(() => setLoading(false));
  }, []);

  const role = user?.role ?? null;

  return <AuthContext value={{ user, role, loading, setUser }}>{children}</AuthContext>;
}
