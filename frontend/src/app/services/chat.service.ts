import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { ChatRequest, ChatResponse, UploadResponse } from '../models/chat.models';

@Injectable({
  providedIn: 'root'
})
export class ChatService {

  private readonly apiUrl = '/api';

  constructor(private http: HttpClient) {}

  // ─── SESIONES ────────────────────────────────────────────────────────────

  createSession(title: string, patientIdentifier?: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/sessions`, {
      title,
      patient_identifier: patientIdentifier
    });
  }

  listSessions(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/sessions`);
  }

  getSession(sessionId: string): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}/sessions/${sessionId}`);
  }

  deleteSession(sessionId: string): Observable<any> {
    return this.http.delete(`${this.apiUrl}/sessions/${sessionId}`);
  }

  updateTask(taskId: string, status: 'completed' | 'archived'): Observable<any> {
    return this.http.patch(`${this.apiUrl}/sessions/tasks/${taskId}`, { status });
  }

  // ─── DOCUMENTOS ──────────────────────────────────────────────────────────

  uploadDocument(file: File, sessionId: string): Observable<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);
    return this.http.post<UploadResponse>(
      `${this.apiUrl}/upload?session_id=${sessionId}`,
      formData
    );
  }

  // ─── CHAT ─────────────────────────────────────────────────────────────────

  getProactiveIntro(filename: string, sessionId: string): Observable<ChatResponse> {
    return this.http.post<ChatResponse>(`${this.apiUrl}/chat/proactive`, {
      filename,
      session_id: sessionId
    });
  }

  sendMessage(request: ChatRequest): Observable<string> {
    return new Observable(observer => {
      fetch(`${this.apiUrl}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request)
      }).then(response => {
        const reader = response.body!.getReader();
        const decoder = new TextDecoder();

        const read = () => {
          reader.read().then(({ done, value }) => {
            if (done) {
              observer.complete();
              return;
            }
            const chunk = decoder.decode(value, { stream: true });
            observer.next(chunk);
            read();
          });
        };

        read();
      }).catch(err => observer.error(err));
    });
  }

  getSuggestedQuestions(assistantResponse: string, sessionId: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/chat/suggested-questions`, {
      assistant_response: assistantResponse,
      session_id: sessionId
    });
  }

  transcribeAudio(audioBlob: Blob): Observable<any> {
    const formData = new FormData();
    formData.append('file', audioBlob, 'audio.webm');
    return this.http.post(`${this.apiUrl}/transcribe`, formData);
  }

  simulateCase(description: string, sessionId: string): Observable<any> {
  return this.http.post(`${this.apiUrl}/simulate`, {
    description,
    session_id: sessionId
  });
}
  
}