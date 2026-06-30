import { Component, OnInit, signal, ViewChild, ElementRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatTooltipModule } from '@angular/material/tooltip';
import { ChatService } from '../../services/chat.service';
import { Message, Source, HistoryMessage } from '../../models/chat.models';
import { UploadComponent } from '../upload/upload';
import { MarkdownComponent } from 'ngx-markdown';

@Component({
  selector: 'app-chat',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatInputModule,
    MatButtonModule,
    MatIconModule,
    MatProgressSpinnerModule,
    MatTooltipModule,
    UploadComponent,
    MarkdownComponent
  ],
  templateUrl: './chat.html',
  styleUrl: './chat.scss'
})
export class ChatComponent implements OnInit {

  @ViewChild('messagesContainer') messagesContainer!: ElementRef;

  messages = signal<Message[]>([]);
  userInput = signal<string>('');
  isLoading = signal<boolean>(false);

  constructor(private chatService: ChatService) {

  }

  ngOnInit(): void {
    this.addWelcomeMessage();
  }

  private addWelcomeMessage(): void {
    this.messages.set([{
      role: 'assistant',
      content: '👋 Hola, soy tu asistente médico. Sube un documento PDF para empezar o hazme una pregunta directamente.',
      sources: []
    }]);
  }

  onDocumentUploaded(filename: string): void {
    this.isLoading.set(true);
    this.addMessage('assistant', '📄 Documento recibido. Analizando contenido...');

    this.chatService.getProactiveIntro(filename).subscribe({
      next: (response) => {
        this.updateLastAssistantMessage(response.intro);
        this.isLoading.set(false);
      },
      error: () => {
        this.updateLastAssistantMessage('Error al analizar el documento.');
        this.isLoading.set(false);
      }
    });
  }

  sendMessage(): void {
    const query = this.userInput().trim();
    if (!query || this.isLoading()) return;

    this.addMessage('user', query);
    this.userInput.set('');
    this.isLoading.set(true);

    const history: HistoryMessage[] = this.messages()
      .filter(m => !m.isStreaming)
      .map(m => ({ role: m.role, content: m.content }));

    const streamingIndex = this.messages().length;
    this.addMessage('assistant', '', [], true);

    let fullContent = '';
    let sources: Source[] = [];

    this.chatService.sendMessage({ query, history }).subscribe({
      next: (chunk: string) => {
        if (chunk.includes('__SOURCES__')) {
          const parts = chunk.split('__SOURCES__');
          fullContent += parts[0];
          try {
            sources = JSON.parse(parts[1]);
          } catch {}
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