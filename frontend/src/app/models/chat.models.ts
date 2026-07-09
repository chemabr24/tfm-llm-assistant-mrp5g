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
  session_id: string;
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

export interface Session {
  id: string;
  title: string;
  patient_identifier?: string;
  created_at: string;
  updated_at?: string;
}

export interface SessionDetail extends Session {
  messages: SessionMessage[];
  tasks: Task[];
  documents: Document[];
}

export interface SessionMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sources: Source[];
  created_at: string;
}

export interface Task {
  id: string;
  content: string;
  status: 'pending' | 'completed' | 'archived';
  created_at: string;
}

export interface Document {
  id: string;
  filename: string;
  chunk_count: string;
  created_at: string;
}