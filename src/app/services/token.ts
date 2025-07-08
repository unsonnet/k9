import { Injectable, signal } from '@angular/core';
import { jwtDecode } from 'jwt-decode';

export interface AuthTokens {
  idToken: string;
  accessToken: string;
  refreshToken?: string;
}

@Injectable({
  providedIn: 'root',
})
export class TokenService {
  private _tokens = signal<AuthTokens | null>(null);
  private _resetSession = signal<{ username: string; session: string } | null>(null);

  set(tokens: AuthTokens): void {
    this._tokens.set(tokens);
    this.clearResetSession();
  }

  setResetSession(username: string, session: string): void {
    this._resetSession.set({ username, session });
    this._tokens.set(null);
  }

  clear(): void {
    this._tokens.set(null);
    this._resetSession.set(null);
  }

  clearResetSession(): void {
    this._resetSession.set(null);
  }

  get accessToken(): string | null {
    return this._tokens()?.accessToken ?? null;
  }

  get idToken(): string | null {
    return this._tokens()?.idToken ?? null;
  }

  get refreshToken(): string | null {
    return this._tokens()?.refreshToken ?? null;
  }

  get resetSession(): string | null {
    return this._resetSession()?.session ?? null;
  }

  get resetUsername(): string | null {
    return this._resetSession()?.username ?? null;
  }

  get all(): AuthTokens | null {
    return this._tokens();
  }

  get expired(): boolean {
    const token = this.accessToken;
    if (!token) return true;

    try {
      const { exp } = jwtDecode<{ exp: number }>(token);
      const now = Math.floor(Date.now() / 1000);
      return exp <= now;
    } catch {
      return true;
    }
  }
}
