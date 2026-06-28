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

  uploadDocument(file: File): Observable<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);
    return this.http.post<UploadResponse>(`${this.apiUrl}/upload`, formData);
  }

  getProactiveIntro(filename: string): Observable<ChatResponse> {
    return this.http.post<ChatResponse>(`${this.apiUrl}/chat/proactive`, { filename });
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
}