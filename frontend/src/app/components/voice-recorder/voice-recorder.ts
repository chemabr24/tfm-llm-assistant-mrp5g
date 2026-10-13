import { Component, Output, EventEmitter, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatTooltipModule } from '@angular/material/tooltip';
import { ChatService } from '../../services/chat.service';

@Component({
  selector: 'app-voice-recorder',
  standalone: true,
  imports: [
    CommonModule,
    MatButtonModule,
    MatIconModule,
    MatTooltipModule
  ],
  templateUrl: './voice-recorder.html',
  styleUrl: './voice-recorder.scss'
})
export class VoiceRecorderComponent {

  @Output() transcriptionReady = new EventEmitter<string>();

  isRecording = signal<boolean>(false);
  isTranscribing = signal<boolean>(false);

  private mediaRecorder: MediaRecorder | null = null;
  private audioChunks: Blob[] = [];

  constructor(private chatService: ChatService) {}

  async toggleRecording(): Promise<void> {
    if (this.isRecording()) {
      this.stopRecording();
    } else {
      await this.startRecording();
    }
  }

  private async startRecording(): Promise<void> {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      this.audioChunks = [];
      this.mediaRecorder = new MediaRecorder(stream);

      this.mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          this.audioChunks.push(event.data);
        }
      };

      this.mediaRecorder.onstop = () => {
        const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm' });
        stream.getTracks().forEach(track => track.stop());
        this.transcribeAudio(audioBlob);
      };

      this.mediaRecorder.start();
      this.isRecording.set(true);
    } catch (error) {
      console.error('Error al acceder al micrófono:', error);
    }
  }

  private stopRecording(): void {
    if (this.mediaRecorder && this.isRecording()) {
      this.mediaRecorder.stop();
      this.isRecording.set(false);
      this.isTranscribing.set(true);
    }
  }

  private transcribeAudio(audioBlob: Blob): void {
    this.chatService.transcribeAudio(audioBlob).subscribe({
      next: (response) => {
        if (response.text) {
          this.transcriptionReady.emit(response.text);
        }
        this.isTranscribing.set(false);
      },
      error: () => {
        this.isTranscribing.set(false);
      }
    });
  }
}