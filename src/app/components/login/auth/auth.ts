import {
  Component,
  computed,
  effect,
  output,
  signal,
} from '@angular/core';
import {
  FormBuilder,
  FormGroup,
  Validators,
  ReactiveFormsModule,
  FormControl,
} from '@angular/forms';
import { CommonModule } from '@angular/common';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { AuthService } from '../../../services/auth';
import { LoginStatus } from '../../../models/login-status';

@Component({
  selector: 'app-login-auth',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    MatFormFieldModule,
    MatInputModule,
    MatButtonModule,
    MatProgressSpinnerModule,
  ],
  templateUrl: './auth.html',
  styleUrl: './auth.scss',
})
export class LoginAuthComponent {
  readonly onSuccess = output<void>();

  loading = signal(false);
  resetMode = signal(false);
  statusMessage = signal<{ text: string; type: 'success' | 'error' } | null>(null);

  newPassword = new FormControl('', Validators.required);
  private newPasswordValue = signal('');

  form: FormGroup;

  constructor(private fb: FormBuilder, private auth: AuthService) {
    this.form = this.fb.group({
      username: ['', Validators.required],
      password: ['', Validators.required],
    });

    this.newPassword.valueChanges.subscribe((val) => {
      this.newPasswordValue.set(val ?? '');
    });
  }

  passwordValid = computed(() => {
    const pwd = this.newPasswordValue();
    return {
      length: pwd.length >= 8,
      upper: /[A-Z]/.test(pwd),
      lower: /[a-z]/.test(pwd),
      digit: /\d/.test(pwd),
      special: /[^A-Za-z0-9]/.test(pwd),
    };
  });

  allValid = computed(() =>
    Object.values(this.passwordValid()).every(Boolean)
  );

  onSubmit(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    const { username, password } = this.form.value;
    this.loading.set(true);
    this.statusMessage.set(null);

    this.auth.login(username, password).subscribe((res) => {
      this.loading.set(false);
      if (res.body === LoginStatus.SUCCESS) {
        this.onSuccess.emit();
      } else if (res.body === LoginStatus.RESET) {
        this.resetMode.set(true);
        this.newPassword.reset();
      } else {
        this.statusMessage.set({
          text: 'Either username or password is incorrect',
          type: 'error',
        });
      }
    });
  }

  submitReset(): void {
    if (!this.allValid()) return;

    const newPwd = this.newPasswordValue();
    this.loading.set(true);
    this.statusMessage.set(null);

    this.auth.reset(newPwd).subscribe((res) => {
      this.loading.set(false);
      this.resetMode.set(false);
      this.form.reset();
      this.newPassword.reset();
      this.statusMessage.set({
        text: res.body
          ? 'Password reset successful. Please log in.'
          : 'Reset failed. Try again.',
        type: res.body ? 'success' : 'error',
      });
    });
  }
}
