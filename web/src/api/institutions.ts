import type { Cause } from "../causes";
import { get, patch, post } from "./client";

export type InstitutionType = "association" | "foundation" | "religious_organization";
export type InstitutionVerdict = "likely_charity" | "nonprofit" | "inactive" | "unlikely";

export interface InstitutionPreview {
  type: InstitutionType;
  cnpj: string;
  legal_name: string;
  trade_name: string | null;
  street: string | null;
  number: string | null;
  complement: string | null;
  neighborhood: string | null;
  city: string;
  state: string;
  postal_code: string | null;
  verdict: InstitutionVerdict;
  reasons: string[];
}

export interface Institution extends InstitutionPreview {
  id: number;
  description: string | null;
  causes: Cause[];
  phone: string | null;
  contact_email: string | null;
  website: string | null;
  instagram: string | null;
  facebook: string | null;
}

export interface OpenNeed {
  id: number;
  title: string;
  description: string;
  quantity: string | null;
}

export interface InstitutionWithNeeds extends Institution {
  open_needs: OpenNeed[];
}

export interface InstitutionChanges {
  trade_name: string;
  description: string;
  causes: Cause[];
  phone: string;
  contact_email: string;
  website: string;
  instagram: string;
  facebook: string;
  street: string;
  number: string;
  complement: string;
  neighborhood: string;
  city: string;
  state: string;
  postal_code: string;
}

export interface NewInstitution extends InstitutionChanges {
  cnpj: string;
}

export function lookupInstitution(cnpj: string): Promise<InstitutionPreview> {
  return get<InstitutionPreview>(`/institutions/lookup?cnpj=${encodeURIComponent(cnpj)}`);
}

export function createInstitution(data: NewInstitution): Promise<Institution> {
  return post<Institution>("/institutions", data);
}

export function listMyInstitutions(): Promise<Institution[]> {
  return get<Institution[]>("/institutions/me");
}

export function getPublicInstitution(id: number): Promise<InstitutionWithNeeds> {
  return get<InstitutionWithNeeds>(`/institutions/${String(id)}`);
}

export function updateInstitution(id: number, changes: InstitutionChanges): Promise<Institution> {
  return patch<Institution>(`/institutions/${String(id)}`, changes);
}
