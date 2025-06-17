import { Component, inject, signal } from '@angular/core';
import { Reference } from '../../models/reference';
import { SearchReferenceComponent } from '../../components/search/reference/reference';
import { SearchProgressComponent } from '../../components/search/progress/progress';
import { Fetch } from '../../services/fetch';
import { v4 as uuidv4 } from 'uuid';
import { firstValueFrom } from 'rxjs';

@Component({
  selector: 'app-search',
  imports: [SearchReferenceComponent, SearchProgressComponent],
  templateUrl: './search.html',
  styleUrl: './search.scss',
})
export class SearchPage {
  readonly loadingMessage = signal('Searching backed items...');
  readonly isErrored = signal(false);

  private readonly fetch = inject(Fetch);

  async onReferenceSubmit(reference: Reference<File>) {
    this.loadingMessage.set('');
    this.isErrored.set(false);

    const job = uuidv4();
    try {
      const apiReference = await this.upload(job, reference);
      const run = await this.initiate(job, apiReference);
      await this.poll(job, run);
    } catch (err) {
      this.loadingMessage.set(
        err instanceof Error ? err.message : 'Fatal error (Unknown)',
      );
      this.isErrored.set(true);
    }

    console.log('Reference submitted:', reference);
  }

  private async upload(
    job: string,
    reference: Reference<File>,
  ): Promise<Reference<string>> {
    this.loadingMessage.set('Uploading references');
    const images: string[] = [];
    for (const file of reference.images) {
      const response = await firstValueFrom(this.fetch.upload(job, file));
      if (response.status !== 200 || !response.body) {
        const err = 'Failed to upload one or more images';
        throw new Error(`${err} (${response.status})`);
      }
      images.push(response.body as string);
    }
    return { ...reference, images: images };
  }

  private async initiate(
    job: string,
    reference: Reference<string>,
  ): Promise<string> {
    this.loadingMessage.set('Initiating server');
    const response = await firstValueFrom(this.fetch.initiate(job, reference));
    if (response.status !== 200 || !response.body) {
      const err = 'Failed to initiate server';
      throw new Error(`${err} (${response.status})`);
    }
    return response.body as string;
  }

  private async poll(
    job: string,
    run: string,
    intervalMs = 10000,
    timeoutMs = 600000,
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
        case 'metric.material':
          this.loadingMessage.set('Packing heavy materials');
          break;
        case 'metric.shape':
          this.loadingMessage.set('Sharpening pointy shapes');
          break;
        case 'metric.color':
          this.loadingMessage.set('Pouring pretty colors');
          break;
        case 'metric.pattern':
          this.loadingMessage.set('Tracing wavey patterns');
          break;
        case 'metric.variation':
          this.loadingMessage.set('Casting light variations');
          break;
        case 'save':
          this.loadingMessage.set('Releasing K9 to the wild');
          break;
        case 'fail':
          throw new Error(`K9 got lost (${response.status})`);
        case 'crash':
          throw new Error(`K9 collapsed (${response.status})`);
      }
    }
    throw new Error('K9 got tired (400)');
  }

  private delay(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }
}
