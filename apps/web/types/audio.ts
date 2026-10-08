export type AudioStatus = "PENDING" | "PROCESSING" | "COMPLETED" | "FAILED";

export interface AudioContent {
  id: string;
  course_id: string;
  course_title?: string;
  section_id: string;
  section_title?: string;
  language: string;
  voice_provider: string;
  voice_id: string;
  script: string;
  storage_key: string;
  duration: number;
  status: AudioStatus;
  error_message?: string;
  audio_url: string | null;
  created_at: string;
  updated_at: string;
}

export interface TTSVoice {
  id: string;
  name: string;
  language: string;
  gender: string;
  provider: string;
  description: string;
}

export interface AudioGenerationRequestPayload {
  voice_provider?: string;
  voice_id?: string;
  language?: string;
  custom_script?: string;
}
