import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { LoginAuthComponent } from '../../components/login/auth/auth';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [LoginAuthComponent],
  templateUrl: './login.html',
  styleUrl: './login.scss',
})
export class LoginPage {
  constructor(private router: Router) {}

  handleSuccess(): void {
    this.router.navigateByUrl('/search');
  }
}
