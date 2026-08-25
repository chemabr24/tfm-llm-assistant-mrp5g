import { Component, Output, EventEmitter, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatRadioModule } from '@angular/material/radio';
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
    MatDialogModule,
    MatRadioModule
  ],
  templateUrl: './create-session.html',
  styleUrl: './create-session.scss'
})
export class CreateSessionComponent {

  title = signal<string>('');
  patientIdentifier = signal<string>('');
  mode = signal<'import' | 'simulate'>('import');
  simulationDescription = signal<string>('');
  isCreating = signal<boolean>(false);

  constructor(
    private chatService: ChatService,
    private dialogRef: MatDialogRef<CreateSessionComponent>
  ) {}

  create(): void {
    if (!this.title().trim()) return;
    if (this.mode() === 'simulate' && !this.simulationDescription().trim()) return;

    this.isCreating.set(true);

    this.chatService.createSession(
      this.title().trim(),
      this.patientIdentifier().trim() || undefined
    ).subscribe({
      next: (session) => {
        if (this.mode() === 'simulate') {
          this.chatService.simulateCase(
            this.simulationDescription().trim(),
            session.id
          ).subscribe({
            next: (result) => {
              this.dialogRef.close({ session, simulationResult: result });
            },
            error: () => {
              this.isCreating.set(false);
            }
          });
        } else {
          this.dialogRef.close({ session, simulationResult: null });
        }
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