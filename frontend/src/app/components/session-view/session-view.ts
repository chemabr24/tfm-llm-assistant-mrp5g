import { Component, OnInit, Input, signal, ViewChild, ElementRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatChipsModule } from '@angular/material/chips';
import { MarkdownComponent } from 'ngx-markdown';
import { ChatService } from '../../services/chat.service';
import { TaskListComponent } from '../task-list/task-list';
import { UploadComponent } from '../upload/upload';
import { Message, Source, Task, HistoryMessage, SessionDetail } from '../../models/chat.models';

@Component({
  selector: 'app-session-view',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatInputModule,
    MatButtonModule,
    MatIconModule,
    MatProgressSpinnerModule,
    MatTooltipModule,
    MatChipsModule,
    MarkdownComponent,
    TaskListComponent,
    UploadComponent
  ],
  templateUrl: './session-view.html',
  styleUrl: './session-view.scss'
})
export class SessionViewComponent implements OnInit {

  @Input() sessionId!: string;
  @ViewChild('messagesContainer') messagesContainer!: ElementRef;

  session = signal<SessionDetail | null>(null);
  messages = signal<Message[]>([]);
  tasks = signal<Task[]>([]);
  suggestedQuestions = signal<string[]>([]);
  userInput = signal<string>('');
  isLoading = signal<boolean>(false);

  constructor(private chatService: ChatService) {}

  ngOnInit(): void {
    this.loadSession();
  }

  loadSession(): void {
    this.chatService.getSession(this.sessionId).subscribe({
      next: (session: SessionDetail) => {
        this.session.set(session);
        this.tasks.set(session.tasks);

        if (session.messages.length === 0) {
          this.addWelcomeMessage();
        } else {
          const msgs: Message[] = session.messages.map(m => ({
            role: m.role,
            content: m.content,
            sources: m.sources || []
          }));
          this.messages.set(msgs);
        }
      }
    });
  }

  private addWelcomeMessage(): void {
    this.messages.set([{
      role: 'assistant',
      content: '👋 Sesión iniciada. Sube un documento PDF para empezar o hazme una consulta directamente.',
      sources: []
    }]);
  }

  onDocumentUploaded(filename: string): void {
    this.isLoading.set(true);
    this.addMessage('assistant', '📄 Documento recibido. Analizando contenido...');

    this.chatService.getProactiveIntro(filename, this.sessionId).subscribe({
      next: (response) => {
        this.updateLastAssistantMessage(response.intro);
        this.extractSuggestedQuestions(response.intro);
        this.isLoading.set(false);
        this.loadSession();
      },
      error: () => {
        this.updateLastAssistantMessage('Error al analizar el documento.');
        this.isLoading.set(false);
      }
    });
  }

  private extractSuggestedQuestions(text: string): void {
    const lines = text.split('\n');
    const questions: string[] = [];
    for (const line of lines) {
      const match = line.match(/^\d+\.\s+\*\*(.+?)\*\*/);
      if (match) {
        questions.push(match[1]);
      }
    }
    this.suggestedQuestions.set(questions.slice(0, 3));
  }

  selectSuggestedQuestion(question: string): void {
    this.userInput.set(question);
    this.suggestedQuestions.set([]);
    this.sendMessage();
  }

  sendMessage(): void {
    const query = this.userInput().trim();
    if (!query || this.isLoading()) return;

    this.addMessage('user', query);
    this.userInput.set('');
    this.isLoading.set(true);
    this.suggestedQuestions.set([]);

    const history: HistoryMessage[] = this.messages()
      .filter(m => !m.isStreaming)
      .map(m => ({ role: m.role, content: m.content }));

    const streamingIndex = this.messages().length;
    this.addMessage('assistant', '', [], true);

    let fullContent = '';
    let sources: Source[] = [];

    this.chatService.sendMessage({
      query,
      session_id: this.sessionId,
      history
    }).subscribe({
      next: (chunk: string) => {
        if (chunk.includes('__SOURCES__')) {
          const parts = chunk.split('__SOURCES__');
          fullContent += parts[0];
          try { sources = JSON.parse(parts[1]); } catch {}
        } else {
          fullContent += chunk;
        }
        this.updateMessageAtIndex(streamingIndex, fullContent, sources, true);
        this.scrollToBottom();
      },
      complete: () => {
        this.updateMessageAtIndex(streamingIndex, fullContent, sources, false);
        this.isLoading.set(false);
        this.scrollToBottom();
        setTimeout(() => this.loadSession(), 2000);
      },
      error: () => {
        this.updateMessageAtIndex(streamingIndex, 'Error al obtener respuesta.', [], false);
        this.isLoading.set(false);
      }
    });
  }

  onEnterKey(event: KeyboardEvent): void {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      this.sendMessage();
    }
  }

  private addMessage(role: 'user' | 'assistant', content: string, sources: Source[] = [], isStreaming = false): void {
    this.messages.update(msgs => [...msgs, { role, content, sources, isStreaming }]);
    this.scrollToBottom();
  }

  private updateLastAssistantMessage(content: string): void {
    this.messages.update(msgs => {
      const updated = [...msgs];
      const last = updated[updated.length - 1];
      if (last?.role === 'assistant') {
        updated[updated.length - 1] = { ...last, content, isStreaming: false };
      }
      return updated;
    });
  }

  private updateMessageAtIndex(index: number, content: string, sources: Source[], isStreaming: boolean): void {
    this.messages.update(msgs => {
      const updated = [...msgs];
      updated[index] = { ...updated[index], content, sources, isStreaming };
      return updated;
    });
  }

  private scrollToBottom(): void {
    setTimeout(() => {
      if (this.messagesContainer) {
        this.messagesContainer.nativeElement.scrollTop =
          this.messagesContainer.nativeElement.scrollHeight;
      }
    }, 50);
  }
}