export interface User {
  id: number;
  email: string;
  username: string;
  visa_category: string;
  role: string;
}

export interface Post {
  id: number;
  title: string;
  body: string;
  visa_category: string;
  author: string;
  gatekeeper_flag: string | null;
  score: number;
  answer_count: number;
  created_at: string;
}

export interface Answer {
  id: number;
  body: string;
  author: string;
  is_best: boolean;
  score: number;
  created_at: string;
}

export interface PostDetail extends Post {
  answers: Answer[];
}

export interface Moderation {
  relevant: boolean;
  reason: string;
  suggested_category: string;
  suggested_title: string;
  harmful: boolean;
  warning: string | null;
}

export interface SearchResultPost {
  id: number;
  title: string;
  snippet: string;
  visa_category: string;
  score: number;
  similarity: number;
}

export interface SearchResponse {
  query: string;
  summary: string;
  grounded: boolean;
  used_post_ids: number[];
  results: SearchResultPost[];
  disclaimer: string;
}

export interface NewsItem {
  id: number;
  source: string;
  title: string;
  url: string;
  summary: string;
  visa_category: string;
  image_url: string | null;
  published_at: string | null;
}
