import { Component } from '@angular/core';
import { LoginAuthComponent } from '../../components/login/auth/auth';

@Component({
  selector: 'app-login',
  imports: [LoginAuthComponent],
  templateUrl: './login.html',
  styleUrl: './login.scss',
})
export class LoginPage {}
