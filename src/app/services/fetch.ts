import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { v4 as uuidv4 } from 'uuid';
import { catchError, map, switchMap } from 'rxjs/operators';
import { Observable, of } from 'rxjs';
import { Reference } from '../models/reference';
import { Thresholds } from '../models/thresholds';
import { Product } from '../models/product';
import { K9Response } from '../models/response';
import { TokenService } from './token';
import { AuthService } from './auth';

@Injectable({
  providedIn: 'root',
})
export class FetchService {
  constructor(
    private http: HttpClient,
    private tokens: TokenService,
    private auth: AuthService,
  ) {}

  private base =
    'https://824xuvy567.execute-api.us-east-2.amazonaws.com/securek9/fetch';

  private withAuthHeaders<T>(
    fn: (headers: HttpHeaders) => Observable<K9Response<T>>,
  ): Observable<K9Response<T>> {
    const token = this.tokens.accessToken;

    // Token exists and not expired? Use it without refreshing.
    if (token && !this.tokens.expired) {
      const headers = new HttpHeaders({ Authorization: `Bearer ${token}` });
      return fn(headers);
    }

    // Otherwise, try refreshing before making the request.
    return this.auth.refresh().pipe(
      switchMap(() => {
        const refreshed = this.tokens.accessToken;
        const headers = new HttpHeaders(
          refreshed ? { Authorization: `Bearer ${refreshed}` } : {},
        );
        return fn(headers);
      }),
    );
  }

  upload(job: string, file: File): Observable<K9Response<string>> {
    const ext = file.name.substring(file.name.lastIndexOf('.'));
    const name = `${uuidv4()}${ext}`;
    const url = `${this.base}/${job}/album/${encodeURIComponent(name)}`;
    return this.withAuthHeaders((headers) =>
      this.http.put(url, file, { observe: 'response', headers }).pipe(
        map((res) => ({ status: res.status, body: name })),
        catchError((err) =>
          of({
            status: err.status || 500,
            body: null,
            error: err.message ?? null,
          }),
        ),
      ),
    );
  }

  initiate(
    job: string,
    reference: Reference<string>,
  ): Observable<K9Response<string>> {
    const url = `${this.base}/${job}`;
    return this.withAuthHeaders((headers) =>
      this.http
        .put(url, reference, {
          responseType: 'text',
          observe: 'response',
          headers,
        })
        .pipe(
          map((res) => ({ status: res.status, body: res.body })),
          catchError((err) =>
            of({
              status: err.status || 500,
              body: null,
              error: err.headers?.get?.('Error-Message') ?? err.message ?? null,
            }),
          ),
        ),
    );
  }

  poll(job: string, run: string): Observable<K9Response<string>> {
    const url = `${this.base}/${job}?run=${run}`;
    return this.withAuthHeaders((headers) =>
      this.http.head(url, { observe: 'response', headers }).pipe(
        map((res) => ({
          status: res.status,
          body: res.headers.get('Stage'),
        })),
        catchError((err) =>
          of({
            status: err.status || 500,
            body: err.headers?.get?.('Stage') || 'crash',
            error: err.headers?.get?.('Error-Message') ?? err.message ?? null,
          }),
        ),
      ),
    );
  }

  summarize(job: string): Observable<K9Response<Reference<string>>> {
    const url = `${this.base}/${job}`;
    return this.withAuthHeaders((headers) =>
      this.http
        .get<Reference<string>>(url, { observe: 'response', headers })
        .pipe(
          map((res) => ({
            status: res.status,
            body: res.body ?? null,
          })),
          catchError((err) =>
            of({
              status: err.status || 500,
              body: null,
              error: err.headers?.get?.('Error-Message') ?? err.message ?? null,
            }),
          ),
        ),
    );
  }

  filter(
    job: string,
    thresholds: Thresholds,
    start: number,
  ): Observable<K9Response<Product[]>> {
    const url = `${this.base}/${job}?start=${start}`;
    return this.withAuthHeaders((headers) =>
      this.http
        .post<Product[]>(url, thresholds, { observe: 'response', headers })
        .pipe(
          map((res) => ({
            status: res.status,
            body: res.body ?? [],
          })),
          catchError((err) =>
            of({
              status: err.status || 500,
              body: null,
              error: err.headers?.get?.('Error-Message') ?? err.message ?? null,
            }),
          ),
        ),
    );
  }
}
