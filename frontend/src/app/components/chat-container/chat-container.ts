import { Component, signal, ViewChild } from '@angular/core';
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

  @ViewChild(SessionListComponent) sessionListRef!: SessionListComponent;
  @ViewChild(SessionViewComponent) sessionViewRef!: SessionViewComponent;
  constructor(private dialog: MatDialog) {}

  onSessionSelected(sessionId: string): void {
    this.selectedSessionId.set(sessionId);
  }

  onCreateSession(): void {
  const dialogRef = this.dialog.open(CreateSessionComponent, {
    width: '500px',
    disableClose: false
  });

  dialogRef.afterClosed().subscribe(result => {
  if (result && result.session) {
    this.selectedSessionId.set(result.session.id);
    this.sessionListRef?.loadSessions();
    
    // Si es una simulación, activar el comportamiento proactivo
    if (result.simulationResult) {
      // Pequeño delay para que el SessionViewComponent se inicialice
      setTimeout(() => {
        this.sessionViewRef?.onDocumentUploaded(result.simulationResult.filename);
      }, 500);
    }
  }
});
}

  
}