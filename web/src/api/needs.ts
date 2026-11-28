import { get, patch, post } from "./client";
import type { OpenNeed } from "./institutions";

export type NeedStatus = "open" | "fulfilled" | "closed";

export interface Need extends OpenNeed {
  status: NeedStatus;
  closed_at: string | null;
}

export interface NeedChanges {
  title: string;
  description: string;
  quantity: string;
}

export function listInstitutionNeeds(institutionId: number): Promise<Need[]> {
  return get<Need[]>(`/institutions/${String(institutionId)}/needs`);
}

export function createNeed(institutionId: number, data: NeedChanges): Promise<Need> {
  return post<Need>(`/institutions/${String(institutionId)}/needs`, data);
}

export function updateNeed(needId: number, changes: NeedChanges): Promise<Need> {
  return patch<Need>(`/needs/${String(needId)}`, changes);
}

export function fulfillNeed(needId: number): Promise<Need> {
  return post<Need>(`/needs/${String(needId)}/fulfill`);
}

export function closeNeed(needId: number): Promise<Need> {
  return post<Need>(`/needs/${String(needId)}/close`);
}
