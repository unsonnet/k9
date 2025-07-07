import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { catchError, map, tap } from 'rxjs/operators';
import { Observable, of } from 'rxjs';
import { K9Response } from '../models/response';
import { TokenService } from './token';

@Injectable({
  providedIn: 'root',
})
export class AuthService {
  constructor(
    private http: HttpClient,
    private tokens: TokenService,
  ) {}

  private base =
    'https://824xuvy567.execute-api.us-east-2.amazonaws.com/securek9/auth';

  login(username: string, password: string): Observable<K9Response<boolean>> {
    const url = `${this.base}/login`;

    return this.http
      .post<any>(url, { username, password }, { observe: 'response' })
      .pipe(
        tap((res) => {
          const session = res.body?.session;
          if (session) {
            this.tokens.setSession(session);
          }
        }),
        map((res) => ({
          status: res.status,
          body: !!res.body?.session,
        })),
        catchError((err) =>
          of({
            status: err.status || 500,
            body: false,
            error: err.error?.message ?? err.message ?? 'Login failed',
          }),
        ),
      );
  }

  verify(code: string): Observable<K9Response<boolean>> {
    const session = this.tokens.session;
    if (!session) {
      return of({
        status: 401,
        body: false,
        error: 'Missing MFA session',
      });
    }

    const url = `${this.base}/verify`;
    return this.http
      .post<any>(url, { code, session }, { observe: 'response' })
      .pipe(
        tap((res) => {
          const body = res.body ?? {};
          if (body.accessToken && body.idToken) {
            this.tokens.set({
              idToken: body.idToken,
              accessToken: body.accessToken,
              refreshToken: body.refreshToken,
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
            error: err.error?.message ?? err.message ?? 'Verification failed',
          }),
        ),
      );
  }

  refresh(): Observable<K9Response<boolean>> {
    const refreshToken = this.tokens.refreshToken;
    if (!refreshToken) {
      return of({
        status: 401,
        body: false,
        error: 'Missing refresh token',
      });
    }

    const url = `${this.base}/refresh`;
    return this.http
      .post<any>(url, { refreshToken }, { observe: 'response' })
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
