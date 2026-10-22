import { api } from "./client";

export type NotificationType =
  | "new_answer"
  | "best_answer"
  | "post_upvote"
  | "answer_upvote";

export interface AppNotification {
  id: string;
  type: NotificationType;
  actor: string;
  message: string;
  postId: number | null;
  answerId: number | null;
  read: boolean;
  createdAt: string;
}

export async function getNotifications(unread = false): Promise<AppNotification[]> {
  const { data } = await api.get<AppNotification[]>("/notifications", {
    params: unread ? { unread: true } : {},
  });
  return data;
}

export async function getUnreadCount(): Promise<number> {
  const { data } = await api.get<{ unread: number }>("/notifications/unread-count");
  return data.unread;
}

export async function markNotificationRead(id: string): Promise<void> {
  await api.post(`/notifications/${id}/read`);
}

export async function markAllNotificationsRead(): Promise<void> {
  await api.post("/notifications/read-all");
}


