export enum Assignee {
  ALEXANDRE = 'Alexandre',
  PEDRO = 'Pedro',
  ROQUELINA = 'Roquelina',
  UNKNOWN = 'Desconhecido'
}

export interface TaskState {
  title: string | null;
  description: string | null;
  dueDate: string | null;
  assignee: Assignee | null;
  status: 'Em Progresso' | 'A Revisar' | 'Completo';
  missingInfo: string[];
  clarificationStrikes: Record<string, number>; // Tracks how many times we asked about a specific field
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'agent';
  text: string;
  audioUrl?: string; // For agent TTS or user playback
  timestamp: number;
}

export interface GeminiResponse {
  replyText: string;
  updatedTask: TaskState;
}