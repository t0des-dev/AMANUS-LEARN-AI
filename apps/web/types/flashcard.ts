export interface FlashcardReviewInfo {
  repetitions: number;
  interval_days: number;
  ease_factor: number;
  last_quality?: number;
  is_due: boolean;
  next_review_at: string | null;
}

export interface FlashcardItem {
  id: string;
  deck: string;
  front: string;
  back: string;
  hint?: string;
  source_citation?: string;
  order: number;
  review_info?: FlashcardReviewInfo | null;
  created_at: string;
}

export interface FlashcardDeckItem {
  id: string;
  organization: string;
  course?: string | null;
  document?: string | null;
  title: string;
  description?: string;
  cards_count: number;
  cards?: FlashcardItem[];
  created_at: string;
  updated_at: string;
}

export interface ReviewSubmitResponse {
  card_id: string;
  quality: number;
  repetitions: number;
  interval_days: number;
  ease_factor: number;
  next_review_at: string;
}
