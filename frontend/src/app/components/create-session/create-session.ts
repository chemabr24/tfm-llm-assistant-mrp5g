import { Component, Output, EventEmitter, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { ChatService } from '../../services/chat.service';

@Component({
  selector: 'app-create-session',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatInputModule,
    MatButtonModule,
    MatIconModule,
    MatDialogModule
  ],
  templateUrl: './create-session.html',
  styleUrl: './create-session.scss'
})
export class CreateSessionComponent {

  title = signal<string>('');
  patientIdentifier = signal<string>('');
  isCreating = signal<boolean>(false);

  constructor(
    private chatService: ChatService,
    private dialogRef: MatDialogRef<CreateSessionComponent>
  ) {}

  create(): void {
    if (!this.title().trim()) return;

    this.isCreating.set(true);
    this.chatService.createSession(
      this.title().trim(),
      this.patientIdentifier().trim() || undefined
    ).subscribe({
      next: (session) => {
        this.dialogRef.close(session);
      },
      error: () => {
        this.isCreating.set(false);
      }
    });
  }

  cancel(): void {
    this.dialogRef.close(null);
  }
}