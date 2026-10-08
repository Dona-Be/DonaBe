export type Role = "donor" | "manager";

export interface PublicUser {
  id: number;
  email: string;
  name: string;
  picture_url: string | null;
  role: Role;
}

export interface PendingSignup {
  email: string;
  name: string;
  picture_url: string | null;
}
