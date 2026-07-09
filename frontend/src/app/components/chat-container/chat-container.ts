import { Component, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { SessionListComponent } from '../session-list/session-list';
import { SessionViewComponent } from '../session-view/session-view';
import { CreateSessionComponent } from '../create-session/create-session';

@Component({
  selector: 'app-chat-container',
  standalone: true,
  imports: [
    CommonModule,
    MatDialogModule,
    MatButtonModule,
    MatIconModule,
    SessionListComponent,
    SessionViewComponent
  ],
  templateUrl: './chat-container.html',
  styleUrl: './chat-container.scss'
})
export class ChatContainerComponent {

  selectedSessionId = signal<string | null>(null);

  constructor(private dialog: MatDialog) {}

  onSessionSelected(sessionId: string): void {
    this.selectedSessionId.set(sessionId);
  }

  onCreateSession(): void {
    const dialogRef = this.dialog.open(CreateSessionComponent, {
      width: '450px',
      disableClose: false
    });

    dialogRef.afterClosed().subscribe(session => {
      if (session) {
        this.selectedSessionId.set(session.id);
      }
    });
  }
}