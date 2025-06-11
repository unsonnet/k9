import { Component, inject, HostListener } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import { v4 as uuidv4 } from 'uuid';
import { Query, Reference } from '../../models/query.model';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { QueryComponent } from '../../components/query/query/query.component';
import { API } from '../../../environments/api';
import { Router } from '@angular/router';
import { Details, Product, Scores } from '../../models/product.model';
import { Thresholds } from '../../models/thresholds.model';
import { packageFilters } from '../../models/thresholds.model';
import { filterGroups } from '../../models/filter.model';
import { mockProducts } from '../../tests/products.data';

@Component({
  selector: 'app-search',
  standalone: true,
  imports: [CommonModule, QueryComponent, MatProgressSpinnerModule, FormsModule],
  templateUrl: './search.page.html',
  styleUrls: ['./search.page.scss'],
})
export class SearchPage {
  private readonly http = inject(HttpClient);
  constructor(private router: Router) {}

  isLoading = false;
  statusText = '';
  errorMessage = '';
  showJobInput = false;
  jobInput = '';

  @HostListener('document:keydown', ['$event'])
  handleKeydown(event: KeyboardEvent): void {
    if (event.ctrlKey && event.key === 'd') {
      event.preventDefault();
      this.showJobInput = true;
    }
  }

  async handleSecretJobFetch(): Promise<void> {
    const job = this.jobInput.trim();
    if (!job) return;

    this.showJobInput = false;
    this.isLoading = true;
    this.errorMessage = '';
    this.statusText = '';

    try {
      const thresholds = packageFilters(filterGroups);
      const products = await this.fetch(job, thresholds);

      // Fetch image URLs and convert to File[]
      const urls: string[] = await firstValueFrom(this.http.get<string[]>(`${API.base}/${job}/album`));
      const filePromises = urls.map(async (url) => {
        const response = await fetch(url);
        const blob = await response.blob();
        const name = decodeURIComponent(url.substring(url.lastIndexOf('/') + 1));
        return new File([blob], name, { type: blob.type });
      });
      const files = await Promise.all(filePromises);

      this.router.navigateByUrl('/results', {
        state: {
          products,
          reference: files, // no query.images, fallback to empty
          job,
        },
      });
    } catch (e: any) {
      this.errorMessage = e?.message || 'Failed to fetch results!';
    } finally {
      this.isLoading = false;
    }
  }

  async startSearch(query: Query): Promise<void> {
    this.isLoading = true;
    this.errorMessage = '';
    this.statusText = '';

    const job = uuidv4();

    try {
      const reference = await this.upload(job, query);
      const run = await this.prepareFetch(job, reference);
      await this.pollFetch(job, run);
      const thresholds = packageFilters(filterGroups);
      const products = await this.fetch(job, thresholds);
      this.router.navigateByUrl('/results', {
        state: {
          products,
          reference: query.images,
          job,
        },
      });
    } catch (error: any) {
      this.errorMessage = error?.message || 'An unexpected error occurred.';
    } finally {
      this.statusText = '';
      this.isLoading = false;
    }
  }

  private async upload(job: string, query: Query): Promise<Reference> {
    const images: string[] = [];
    try {
      this.statusText = 'Uploading references...';
      await Promise.all(
        query.images.map((file: File) => {
          const extension = file.name.substring(file.name.lastIndexOf('.'));
          const filename = `${uuidv4()}${extension}`;
          const url = `${API.base}/${job}/album/${encodeURIComponent(filename)}`;
          images.push(filename);
          return firstValueFrom(this.http.put(url, file));
        }),
      );
      return {
        ...query,
        material: query.material?.toLowerCase?.() ?? query.material,
        images: images,
      };
    } catch (err) {
      throw new Error('Failed to upload one or more images! (500)');
    }
  }

  private async prepareFetch(
    job: string,
    reference: Reference,
  ): Promise<string> {
    const url = `${API.base}/${job}/fetch`;
    try {
      this.statusText = 'Initiating server...';
      return await firstValueFrom(
        this.http.put(url, reference, { responseType: 'text' }),
      );
    } catch {
      throw new Error('Failed to initiate server! (500)');
    }
  }

  private async pollFetch(
    job: string,
    run: string,
    intervalMs = 10000,
    timeoutMs = 600000,
  ): Promise<void> {
    const url = `${API.base}/${job}/fetch?run=${run}`;
    const start = Date.now();
    while (Date.now() - start < timeoutMs) {
      await this.delay(intervalMs);
      try {
        const response = await firstValueFrom(
          this.http.head(url, { observe: 'response' }),
        );
        const stage = response.headers.get('Stage');

        if (response.status === 200) {
          return;
        }

        if (response.status === 202) {
          switch (stage) {
            case 'start':
              this.statusText = 'Building universe...';
              break;
            case 'load':
              this.statusText = 'Preparing K9 for the wild...';
              break;
            case 'metric.material':
              this.statusText = 'Packing heavy materials...';
              break;
            case 'metric.shape':
              this.statusText = 'Sharpening pointy shapes...';
              break;
            case 'metric.color':
              this.statusText = 'Pouring pretty colors...';
              break;
            case 'metric.pattern':
              this.statusText = 'Tracing wavey patterns...';
              break;
            case 'metric.variation':
              this.statusText = 'Casting light variations...';
              break;
            case 'save':
              this.statusText = 'Releasing K9 to the wild...';
              break;
          }
          continue;
        }
      } catch (e: any) {
        const stage = e?.headers?.get?.('x-stage') ?? 'crash';

        if (stage === 'fail') {
          throw new Error(`K9 got lost! (${e.status || 'unknown'})`);
        } else {
          throw new Error(`Universe imploded! (${e.status || 'unknown'})`);
        }
      }
    }
    throw new Error('K9 got tired! (400)');
  }

  private async fetch(job: string, thresholds: Thresholds): Promise<Product[]> {
    const url = `${API.base}/${job}/fetch`;
    try {
      this.statusText = 'Fetching results...';
      const raw = await firstValueFrom(this.http.post<any[]>(url, thresholds));
      const products: Product[] = raw.map((p) => {
        const { id, store, name, images, color, pattern, variation, ...rest } = p;

        const scores: Scores = {};
        if (color) scores['color'] = color;
        if (pattern) scores['pattern'] = pattern;
        if (variation) scores['variation'] = variation;

        const details: Details = rest;

        return {
          id,
          store,
          name,
          images,
          scores,
          details,
        };
      });
      return products;
    } catch {
      throw new Error('Failed to fetch results! (500)');
    }
  }

  private delay(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  closeError(): void {
    this.errorMessage = '';
  }
}
