import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatSelectModule } from '@angular/material/select';
import { MatSnackBarModule, MatSnackBar } from '@angular/material/snack-bar';
import { Router } from '@angular/router';
import { ChatService } from '../../services/chat.service';

@Component({
  selector: 'app-profile',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatInputModule,
    MatButtonModule,
    MatIconModule,
    MatSelectModule,
    MatSnackBarModule
  ],
  templateUrl: './profile.html',
  styleUrl: './profile.scss'
})
export class ProfileComponent implements OnInit {

  email = signal<string>('');
  notificationFrequency = signal<string>('weekly');
  isSaving = signal<boolean>(false);

  constructor(
    private chatService: ChatService,
    private router: Router,
    private snackBar: MatSnackBar
  ) {}

  ngOnInit(): void {
    const email = localStorage.getItem('user_email') || '';
    const preferences = JSON.parse(localStorage.getItem('user_preferences') || '{}');
    this.email.set(email);
    this.notificationFrequency.set(preferences.notification_frequency || 'weekly');
  }

  saveProfile(): void {
    const userId = localStorage.getItem('user_id');
    if (!userId) return;

    this.isSaving.set(true);

    const preferences = {
      notification_frequency: this.notificationFrequency()
    };

    this.chatService.updateProfile(userId, preferences).subscribe({
      next: () => {
        localStorage.setItem('user_preferences', JSON.stringify(preferences));
        this.isSaving.set(false);
        this.snackBar.open('Perfil actualizado correctamente', 'Cerrar', { duration: 3000 });
      },
      error: () => {
        this.isSaving.set(false);
        this.snackBar.open('Error al guardar el perfil', 'Cerrar', { duration: 3000 });
      }
    });
  }

  logout(): void {
    localStorage.removeItem('user_id');
    localStorage.removeItem('user_email');
    localStorage.removeItem('user_preferences');
    this.router.navigate(['/auth/login']);
  }

  goBack(): void {
    this.router.navigate(['/']);
  }
}