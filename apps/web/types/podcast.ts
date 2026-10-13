export interface PodcastHost {
  name: string;
  role: "host" | "expert";
  voice_id?: string;
}

export interface PodcastTurn {
  speaker: string;
  role: "host" | "expert";
  text: string;
}

export interface PodcastEpisodeItem {
  id: string;
  organization_id: string;
  document_id?: string | null;
  document_title?: string | null;
  course_id?: string | null;
  course_title?: string | null;
  title: string;
  description: string;
  language: string;
  hosts: PodcastHost[];
  turns: PodcastTurn[];
  key_takeaways: string[];
  duration: number;
  status: "PENDING" | "PROCESSING" | "COMPLETED" | "FAILED";
  audio_url?: string | null;
  created_at: string;
  updated_at: string;
}

export interface PodcastGenerateRequest {
  document_id?: string;
  course_id?: string;
  language?: string;
  level?: string;
  focus?: string;
  voice_provider?: string;
}
