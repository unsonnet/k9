import { Component, HostListener, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { v4 as uuidv4 } from 'uuid';
import { firstValueFrom } from 'rxjs';

import { Reference } from '../../models/reference';
import { FetchService } from '../../services/fetch';

import { SearchReferenceComponent } from '../../components/search/reference/reference';
import { SearchProgressComponent } from '../../components/search/progress/progress';

import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';

@Component({
  selector: 'app-search',
  standalone: true,
  imports: [
    SearchReferenceComponent,
    SearchProgressComponent,
    MatProgressSpinnerModule,
    MatFormFieldModule,
    MatInputModule,
    MatButtonModule,
    FormsModule,
  ],
  templateUrl: './search.html',
  styleUrl: './search.scss',
})
export class SearchPage {
  // ─── Signals ─────────────────────────────────────────────────────
  readonly loadingMessage = signal('');
  readonly errorMessage = signal('');

  // ─── UI State ─────────────────────────────────────────────────────
  hasOverlay = false;
  jobId = '';

  // ─── Dependencies ────────────────────────────────────────────────
  private readonly fetch = inject(FetchService);
  private readonly router = inject(Router);

  // ─── Overlay Keyboard Shortcut ───────────────────────────────────
  @HostListener('document:keydown', ['$event'])
  onKeydown(event: KeyboardEvent) {
    if (event.ctrlKey && event.key.toLowerCase() === 'd') {
      event.preventDefault();
      this.hasOverlay = true;
    }
  }

  closeOverlay() {
    this.hasOverlay = false;
  }

  // ─── Public Submission Handlers ──────────────────────────────────
  async onJobIdSubmit() {
    const job = this.jobId.trim();
    if (!job) return;

    try {
      this.loadingMessage.set('Summoning past K9');
      this.errorMessage.set('');
      this.hasOverlay = false;

      const summary = await this.summarize(job);
      await this.router.navigateByUrl('/results', {
        state: { reference: summary, job },
      });
    } catch (err) {
      this.loadingMessage.set('');
      this.errorMessage.set('Invalid Job ID');
    } finally {
      this.hasOverlay = false;
    }
  }

  async onReferenceSubmit(reference: Reference<File>) {
    this.loadingMessage.set('');
    this.errorMessage.set('');

    const job = uuidv4();
    this.loadingMessage.set('testing');

    try {
      const apiReference = await this.upload(job, reference);
      const run = await this.initiate(job, apiReference);
      await this.poll(job, run);
      const summary = await this.summarize(job);
      await this.router.navigateByUrl('/results', {
        state: { reference: summary, job },
      });
    } catch (err) {
      this.loadingMessage.set('');
      const msg = err instanceof Error ? err.message : 'Fatal error (Unknown)';
      this.errorMessage.set(msg);
    }

    console.log('Reference submitted:', reference);
  }

  // ─── Private API Pipeline ────────────────────────────────────────
  private async upload(
    job: string,
    reference: Reference<File>,
  ): Promise<Reference<string>> {
    this.loadingMessage.set('Uploading references');
    const images: string[] = [];

    for (const file of reference.images) {
      const response = await firstValueFrom(this.fetch.upload(job, file));
      if (response.status !== 200 || !response.body) {
        throw new Error(`Failed to upload (${response.status})`);
      }
      images.push(response.body as string);
    }

    return { ...reference, images };
  }

  private async initiate(
    job: string,
    reference: Reference<string>,
  ): Promise<string> {
    this.loadingMessage.set('Initiating server');
    const response = await firstValueFrom(this.fetch.initiate(job, reference));
    if (response.status !== 200 || !response.body) {
      throw new Error(`Failed to initiate (${response.status})`);
    }
    return response.body as string;
  }

  private async poll(
    job: string,
    run: string,
    intervalMs = 10_000,
    timeoutMs = 600_000,
  ): Promise<void> {
    this.loadingMessage.set('Initiating server');
    const start = Date.now();

    while (Date.now() - start < timeoutMs) {
      await this.delay(intervalMs);
      const response = await firstValueFrom(this.fetch.poll(job, run));
      if (response.status === 200) return;

      switch (response.body as string) {
        case 'start':
          this.loadingMessage.set('Building universe');
          break;
        case 'load':
          this.loadingMessage.set('Preparing K9 for the wild');
          break;
        case 'metric.product.material':
          this.loadingMessage.set('Packing heavy materials');
          break;
        case 'metric.product.shape':
          this.loadingMessage.set('Sharpening pointy shapes');
          break;
        case 'metric.product.color':
          this.loadingMessage.set('Pouring pretty colors');
          break;
        case 'metric.product.pattern':
          this.loadingMessage.set('Tracing wavey patterns');
          break;
        case 'metric.image.color':
          this.loadingMessage.set('[Legacy] Pouring pretty colors');
          break;
        case 'metric.image.pattern':
          this.loadingMessage.set('[Legacy] Tracing wavey patterns');
          break;
        case 'metric.image.variation':
          this.loadingMessage.set('[Legacy] Casting light variations');
          break;
        case 'save':
          this.loadingMessage.set('Releasing K9 to the wild');
          break;
        case 'fail':
          throw new Error(`K9 got confused (${response.status})`);
        case 'crash':
          throw new Error(`K9 collapsed (${response.status})`);
      }
    }

    throw new Error('K9 got tired (400)');
  }

  private async summarize(job: string): Promise<Reference<string>> {
    const response = await firstValueFrom(this.fetch.summarize(job));
    if (response.status !== 200 || !response.body) {
      throw new Error(`K9 got lost (${response.status})`);
    }
    return response.body;
  }

  private delay(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }
}
