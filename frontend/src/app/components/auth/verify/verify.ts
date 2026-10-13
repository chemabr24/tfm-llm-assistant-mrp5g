import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatButtonModule } from '@angular/material/button';
import { ChatService } from '../../../services/chat.service';
import { MatIconModule } from '@angular/material/icon';


@Component({
  selector: 'app-verify',
  standalone: true,
  imports: [
    CommonModule,
    MatProgressSpinnerModule,
    MatButtonModule,
    MatIconModule
  ],
  templateUrl: './verify.html',
  styleUrl: './verify.scss'
})
export class Verify implements OnInit {

  isVerifying = signal<boolean>(true);
  error = signal<string | null>(null);

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private chatService: ChatService
  ) {}

  ngOnInit(): void {
    const token = this.route.snapshot.queryParamMap.get('token');
    if (!token) {
      this.error.set('Token no válido.');
      this.isVerifying.set(false);
      return;
    }

    this.chatService.verifyMagicLink(token).subscribe({
      next: (user) => {
        localStorage.setItem('user_id', user.user_id);
        localStorage.setItem('user_email', user.email);
        localStorage.setItem('user_preferences', JSON.stringify(user.preferences));
        this.router.navigate(['/']);
      },
      error: () => {
        this.error.set('El enlace no es válido o ha caducado.');
        this.isVerifying.set(false);
      }
    });
  }

  goToLogin(): void {
    this.router.navigate(['/auth/login']);
  }
}