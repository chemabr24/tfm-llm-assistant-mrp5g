import { Component, EventEmitter, Output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatSnackBarModule, MatSnackBar } from '@angular/material/snack-bar';
import { ChatService } from '../../services/chat.service';
import { UploadResponse } from '../../models/chat.models';

@Component({
  selector: 'app-upload',
  standalone: true,
  imports: [
    CommonModule,
    MatButtonModule,
    MatIconModule,
    MatProgressBarModule,
    MatSnackBarModule
  ],
  templateUrl: './upload.html',
  styleUrl: './upload.scss'
})
export class UploadComponent {

  @Output() documentUploaded = new EventEmitter<string>();

  selectedFile: File | null = null;
  isUploading = false;
  uploadProgress = false;

  constructor(
    private chatService: ChatService,
    private snackBar: MatSnackBar
  ) {}

  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files[0]) {
      const file = input.files[0];
      if (file.type !== 'application/pdf') {
        this.snackBar.open('Solo se permiten archivos PDF', 'Cerrar', { duration: 3000 });
        return;
      }
      this.selectedFile = file;
    }
  }

  uploadFile(): void {
    if (!this.selectedFile) return;

    this.isUploading = true;
    this.uploadProgress = true;

    this.chatService.uploadDocument(this.selectedFile).subscribe({
      next: (response: UploadResponse) => {
        this.snackBar.open(
          `✓ ${response.chunks_indexados} fragmentos indexados`,
          'Cerrar',
          { duration: 4000 }
        );
        this.documentUploaded.emit(this.selectedFile!.name);
        this.selectedFile = null;
        this.isUploading = false;
        this.uploadProgress = false;
      },
      error: () => {
        this.snackBar.open('Error al subir el documento', 'Cerrar', { duration: 3000 });
        this.isUploading = false;
        this.uploadProgress = false;
      }
    });
  }
}