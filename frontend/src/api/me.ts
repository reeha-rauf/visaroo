import type { Post } from "./types";
import { api } from "./client";

/** The current user's own question (owner view — includes is_anonymous for badging). */
export interface MyPost {
  id: number;
  title: string;
  visa_category: string;
  is_anonymous: boolean;
  score: number;
  answer_count: number;
  created_at: string;
}

/** The current user's own answer, linked to its parent question. */
export interface MyAnswer {
  id: number;
  body: string;
  is_anonymous: boolean;
  is_best: boolean;
  score: number;
  created_at: string;
  post_id: number;
  post_title: string;
}

export async function getMyPosts(): Promise<MyPost[]> {
  const { data } = await api.get<MyPost[]>("/me/posts");
  return data;
}

export async function getMyAnswers(): Promise<MyAnswer[]> {
  const { data } = await api.get<MyAnswer[]>("/me/answers");
  return data;
}

/**
 * Adapt a MyPost into the shape PostCard expects (the `Post` type), so we can reuse the
 * existing card for "My questions". The author is shown as the owner-facing label.
 */
export function myPostToCard(p: MyPost, username: string): Post {
  return {
    id: p.id,
    title: p.title,
    body: "",
    visa_category: p.visa_category,
    author: p.is_anonymous ? "You (anonymous)" : username,
    gatekeeper_flag: null,
    score: p.score,
    answer_count: p.answer_count,
    created_at: p.created_at,
  };
}
