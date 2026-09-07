import { Component, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { ChatService } from '../../../services/chat.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatInputModule,
    MatButtonModule,
    MatIconModule,
    MatProgressSpinnerModule
  ],
  templateUrl: './login.html',
  styleUrl: './login.scss'
})
export class Login {

  email = signal<string>('');
  isSending = signal<boolean>(false);
  sent = signal<boolean>(false);
  error = signal<string | null>(null);

  constructor(private chatService: ChatService) {}

  requestLink(): void {
    if (!this.email().trim()) return;

    this.isSending.set(true);
    this.error.set(null);

    this.chatService.requestMagicLink(this.email().trim()).subscribe({
      next: () => {
        this.sent.set(true);
        this.isSending.set(false);
      },
      error: () => {
        this.error.set('Error al enviar el enlace. Inténtalo de nuevo.');
        this.isSending.set(false);
      }
    });
  }
}