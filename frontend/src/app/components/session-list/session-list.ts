import { Component, OnInit, Output, EventEmitter, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatListModule } from '@angular/material/list';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatDividerModule } from '@angular/material/divider';
import { ChatService } from '../../services/chat.service';
import { Session } from '../../models/chat.models';

@Component({
  selector: 'app-session-list',
  standalone: true,
  imports: [
    CommonModule,
    MatListModule,
    MatIconModule,
    MatButtonModule,
    MatTooltipModule,
    MatDividerModule
  ],
  templateUrl: './session-list.html',
  styleUrl: './session-list.scss'
})
export class SessionListComponent implements OnInit {

  @Output() sessionSelected = new EventEmitter<string>();
  @Output() createSessionClicked = new EventEmitter<void>();

  sessions = signal<Session[]>([]);
  selectedSessionId = signal<string | null>(null);

  constructor(private chatService: ChatService) {}

  ngOnInit(): void {
    this.loadSessions();
  }

  loadSessions(): void {
    this.chatService.listSessions().subscribe({
      next: (sessions) => this.sessions.set(sessions),
      error: () => console.error('Error al cargar sesiones')
    });
  }

  selectSession(sessionId: string): void {
    this.selectedSessionId.set(sessionId);
    this.sessionSelected.emit(sessionId);
  }

  onCreateSession(): void {
    this.createSessionClicked.emit();
  }

  deleteSession(event: Event, sessionId: string): void {
    event.stopPropagation();
    this.chatService.deleteSession(sessionId).subscribe({
      next: () => {
        this.sessions.update(sessions => sessions.filter(s => s.id !== sessionId));
        if (this.selectedSessionId() === sessionId) {
          this.selectedSessionId.set(null);
        }
      },
      error: () => console.error('Error al eliminar sesión')
    });
  }
}