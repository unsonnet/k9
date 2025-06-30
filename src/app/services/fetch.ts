import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { v4 as uuidv4 } from 'uuid';
import { catchError, map } from 'rxjs/operators';
import { Observable, of } from 'rxjs';
import { Reference } from '../models/reference';
import { Thresholds } from '../models/thresholds';
import { Product } from '../models/product';

export type FetchResponse<T> = {
  status: number;
  body: T | null;
};

@Injectable({
  providedIn: 'root',
})
export class Fetch {
  constructor(private http: HttpClient) {}

  private base = 'https://824xuvy567.execute-api.us-east-2.amazonaws.com/k9';

  upload(job: string, file: File): Observable<FetchResponse<string>> {
    const ext = file.name.substring(file.name.lastIndexOf('.'));
    const name = `${uuidv4()}${ext}`;
    const url = `${this.base}/${job}/album/${encodeURIComponent(name)}`;
    return this.http.put(url, file, { observe: 'response' }).pipe(
      map((response) => ({ status: response.status, body: name })),
      catchError((err) => of({ status: err.status || 500, body: null })),
    );
  }

  initiate(
    job: string,
    reference: Reference<string>,
  ): Observable<FetchResponse<string>> {
    const url = `${this.base}/${job}/fetch`;
    return this.http
      .put(url, reference, { responseType: 'text', observe: 'response' })
      .pipe(
        map((response) => ({ status: response.status, body: response.body })),
        catchError((err) => of({ status: err.status || 500, body: null })),
      );
  }

  poll(job: string, run: string): Observable<FetchResponse<string>> {
    const url = `${this.base}/${job}/fetch?run=${run}`;
    return this.http.head(url, { observe: 'response' }).pipe(
      map((response) => ({
        status: response.status,
        body: response.headers.get('Stage'),
      })),
      catchError((err) =>
        of({
          status: err.status || 500,
          body: err.headers.get('Stage') || 'crash',
        }),
      ),
    );
  }

  summarize(job: string): Observable<FetchResponse<Reference<string>>> {
    const url = `${this.base}/${job}/fetch`;
    return this.http.get<Reference<string>>(url, { observe: 'response' }).pipe(
      map((response) => ({
        status: response.status,
        body: response.body ?? null,
      })),
      catchError((err) =>
        of({
          status: err.status || 500,
          body: null,
        }),
      ),
    );
  }

  filter(
    job: string,
    thresholds: Thresholds,
    start: number,
  ): Observable<FetchResponse<Product[]>> {
    const url = `${this.base}/${job}/fetch?start=${start}`;
    return this.http
      .post<Product[]>(url, thresholds, { observe: 'response' })
      .pipe(
        map((response) => ({
          status: response.status,
          body: response.body ?? [],
        })),
        catchError((err) =>
          of({
            status: err.status || 500,
            body: null,
          }),
        ),
      );
  }
}
