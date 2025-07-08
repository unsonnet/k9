import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { catchError, map, tap } from 'rxjs/operators';
import { Observable, of } from 'rxjs';
import { K9Response } from '../models/response';
import { TokenService } from './token';
import { LoginStatus } from '../models/login-status';

@Injectable({
  providedIn: 'root',
})
export class AuthService {
  constructor(
    private http: HttpClient,
    public tokens: TokenService,
  ) {}

  private base =
    'https://824xuvy567.execute-api.us-east-2.amazonaws.com/securek9/auth';

  login(
    username: string,
    password: string,
  ): Observable<K9Response<LoginStatus>> {
    const url = `${this.base}/login`;

    return this.http
      .post<any>(url, { username, password }, { observe: 'response' })
      .pipe(
        tap((res) => {
          const body = res.body ?? {};
          if (res.status === 200 && body.accessToken && body.idToken) {
            this.tokens.set({
              idToken: body.idToken,
              accessToken: body.accessToken,
              refreshToken: body.refreshToken,
            });
          } else if (res.status === 202 && body.session && body.username) {
            this.tokens.setResetSession(body.username, body.session);
          }
        }),
        map((res) => {
          if (res.status === 200)
            return { status: 200, body: LoginStatus.SUCCESS };
          if (res.status === 202)
            return { status: 202, body: LoginStatus.RESET };
          return { status: res.status, body: LoginStatus.DENIED };
        }),
        catchError((err) =>
          of({
            status: err.status || 500,
            body: LoginStatus.DENIED,
            error: err.error?.message ?? err.message ?? 'Login failed',
          }),
        ),
      );
  }

  reset(newPassword: string): Observable<K9Response<boolean>> {
    const session = this.tokens.resetSession;
    const username = this.tokens.resetUsername;
    if (!session || !username) {
      return of({
        status: 400,
        body: false,
        error: 'Missing session or username',
      });
    }

    const url = `${this.base}/reset`;
    return this.http
      .post<any>(
        url,
        { username, newPassword, session },
        { observe: 'response' },
      )
      .pipe(
        tap(() => this.tokens.clearResetSession()),
        map((res) => ({
          status: res.status,
          body: res.status === 200,
        })),
        catchError((err) =>
          of({
            status: err.status || 500,
            body: false,
            error: err.error?.message ?? err.message ?? 'Password reset failed',
          }),
        ),
      );
  }

  refresh(): Observable<K9Response<boolean>> {
    const refreshToken = this.tokens.refreshToken;
    const username = this.tokens.resetUsername; // if needed
    if (!refreshToken || !username) {
      return of({
        status: 401,
        body: false,
        error: 'Missing refresh token or username',
      });
    }

    const url = `${this.base}/refresh`;
    return this.http
      .post<any>(url, { refreshToken, username }, { observe: 'response' })
      .pipe(
        tap((res) => {
          const body = res.body ?? {};
          if (body.accessToken && body.idToken) {
            this.tokens.set({
              idToken: body.idToken,
              accessToken: body.accessToken,
              refreshToken,
            });
          }
        }),
        map((res) => ({
          status: res.status,
          body: !!res.body?.accessToken,
        })),
        catchError((err) =>
          of({
            status: err.status || 500,
            body: false,
            error: err.error?.message ?? err.message ?? 'Token refresh failed',
          }),
        ),
      );
  }
}
