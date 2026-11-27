import { get, post } from "./client";

export type NotificationType =
  "intent_registered" | "intent_cancelled" | "intent_delivered" | "intent_status_changed";

export interface Notification {
  id: number;
  type: NotificationType;
  message: string;
  donation_intent_id: number;
  read_at: string | null;
  created_at: string;
}

interface UnreadCount {
  count: number;
}

// The API answers 20 notifications per page.
export const NOTIFICATIONS_PAGE_SIZE = 20;

export function listNotifications(page: number): Promise<Notification[]> {
  return get<Notification[]>(`/notifications?page=${String(page)}`);
}

export async function countUnreadNotifications(): Promise<number> {
  const { count } = await get<UnreadCount>("/notifications/unread-count");
  return count;
}

export function markNotificationAsRead(id: number): Promise<void> {
  return post<undefined>(`/notifications/${String(id)}/read`);
}

export function markAllNotificationsAsRead(): Promise<void> {
  return post<undefined>("/notifications/read-all");
}
