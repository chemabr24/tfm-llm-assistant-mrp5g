export interface Message {
  role: 'user' | 'assistant';
  content: string;
  sources?: Source[];
  isStreaming?: boolean;
}

export interface Source {
  source: string;
  page: number;
  score: number;
}

export interface ChatRequest {
  query: string;
  history: HistoryMessage[];
}

export interface HistoryMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface ChatResponse {
  intro: string;
}

export interface UploadResponse {
  filename: string;
  chunks_indexados: number;
  mensaje: string;
}