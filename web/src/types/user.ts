import type { Cause } from "../causes";

export type Role = "donor" | "manager";

export interface Profile {
  email: string;
  name: string;
  picture_url: string | null;
  phone: string | null;
  role: Role | null;
  postal_code: string | null;
  preferred_causes: Cause[] | null;
}
