import { ApplicationConfig, provideZoneChangeDetection } from '@angular/core';
import { provideHttpClient } from '@angular/common/http';
import { provideMarkdown } from 'ngx-markdown';
import { provideRouter, Routes } from '@angular/router';
import { ChatContainerComponent } from './components/chat-container/chat-container';
import { Verify } from './components/auth/verify/verify';
import { Login } from './components/auth/login/login';
import { authGuard } from './guards/auth.guard';
import { ProfileComponent } from './components/profile/profile';

const routes: Routes = [
  { path: '', component: ChatContainerComponent, canActivate: [authGuard] },
  { path: 'profile', component: ProfileComponent, canActivate: [authGuard] },
  { path: 'auth/verify', component: Verify },
  { path: 'auth/login', component: Login },
  { path: '**', redirectTo: '' }
];

export const appConfig: ApplicationConfig = {
  providers: [
    provideZoneChangeDetection({ eventCoalescing: true }),
    provideHttpClient(),
    provideMarkdown(),
    provideRouter(routes)
  ]
};
