import { inject } from '@angular/core';
import { Router, CanActivateFn } from '@angular/router';

export const authGuard: CanActivateFn = () => {
  const router = inject(Router);
  const userId = localStorage.getItem('user_id');

  if (!userId) {
    router.navigate(['/auth/login']);
    return false;
  }

  return true;
};