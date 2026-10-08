import { useEffect, useState, type ReactNode } from "react";
import { readCurrentUser } from "../api/auth";
import type { PublicUser } from "../types/user";
import { AuthContext } from "./AuthContext";

export function AuthProvider({ children }: Readonly<{ children: ReactNode }>) {
  const [user, setUser] = useState<PublicUser | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    readCurrentUser()
      .then(setUser)
      .catch(() => setUser(null))
      .finally(() => setLoading(false));
  }, []);

  return <AuthContext value={{ user, loading, setUser }}>{children}</AuthContext>;
}
