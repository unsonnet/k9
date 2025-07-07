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
  private _session = signal<string | null>(null);

  set(tokens: AuthTokens): void {
    this._tokens.set(tokens);
    this._session.set(null); // clear session once tokens are issued
  }

  setSession(session: string): void {
    this._session.set(session);
    this._tokens.set(null); // clear tokens until MFA is complete
  }

  clear(): void {
    this._tokens.set(null);
    this._session.set(null);
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

  get session(): string | null {
    return this._session();
  }

  get all(): AuthTokens | null {
    return this._tokens();
  }

  get isAccessTokenExpired(): boolean {
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
