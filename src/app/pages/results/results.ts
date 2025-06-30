import { Component, computed, inject, input, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatButtonModule } from '@angular/material/button';

import { ResultsThresholdsComponent } from '../../components/results/thresholds/thresholds';
import { ResultsGridComponent } from '../../components/results/grid/grid';
import { ResultsReferenceComponent } from '../../components/results/reference/reference';
import { Thresholds } from '../../models/thresholds';
import { Product } from '../../models/product';
import { ProductPage } from '../product/product';
import { Export } from '../../services/export';
import { Reference } from '../../models/reference';
import { Router } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { Fetch } from '../../services/fetch';

@Component({
  selector: 'app-results',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    ResultsThresholdsComponent,
    ResultsGridComponent,
    ResultsReferenceComponent,
    ProductPage,
    MatProgressBarModule,
    MatButtonModule,
  ],
  templateUrl: './results.html',
  styleUrls: ['./results.scss'],
})
export class ResultsPage {
  readonly reference = signal<Reference<string>>({
    type: '',
    material: '',
    length: null,
    width: null,
    thickness: null,
    images: [],
  });
  readonly job = signal<string>('');

  constructor(private exportService: Export) {
    const state = inject(Router).getCurrentNavigation()?.extras.state as
      | {
          reference: Reference<string>;
          job: string;
        }
      | undefined;

    if (!state?.reference || !state?.job) {
      throw new Error('Results page loaded without reference or job');
    }

    this.reference.set(state.reference);
    this.job.set(state.job);
  }

  private readonly fetch = inject(Fetch);

  readonly exportUrl = signal<string | null>(null);
  readonly loading = signal(false);
  readonly loadingMessage = signal<string | null>(null);

  readonly products = signal<Product[]>([]);
  readonly orderBy = signal<'score' | 'name' | 'starred'>('score');
  readonly activeProduct = signal<Product | null>(null);
  readonly starredCount = computed(
    () => this.sortedProducts().filter((p) => p.starred).length,
  );

  readonly exportEnabled = computed(() =>
    this.sortedProducts().some((p) => p.starred),
  );

  readonly sortedProducts = computed(() => {
    const products = [...this.products()];
    const key = this.orderBy();

    return products.sort((a, b) => {
      if (key === 'score') return 0;
      if (key === 'name')
        return a.description.name.localeCompare(b.description.name);
      if (key === 'starred') {
        return Number(b.starred ?? false) - Number(a.starred ?? false);
      }
      return 0;
    });
  });

  async handleApply(thresholds: Thresholds) {
    this.loadingMessage.set('Filtering products...');
    this.loading.set(true);

    try {
      const job = this.job();
      const response = await firstValueFrom(
        this.fetch.filter(job, thresholds, 0),
      );
      if (response.status !== 200 || !response.body) {
        throw new Error(`Failed to filter products (${response.status})`);
      }
      this.products.set(response.body);
      this.loading.set(false);
    } catch (err) {
      console.error(err);
      this.loadingMessage.set('An error occurred while filtering.');
    }
  }

  async handleExport() {
    const starred = this.products().filter((p) => p.starred);
    if (starred.length === 0) return;

    this.loadingMessage.set('Packaging products...');
    this.loading.set(true);
    this.exportUrl.set(null);

    const blob = await this.exportService.exportProducts(
      this.reference(),
      starred,
    );
    const url = URL.createObjectURL(blob);
    this.exportUrl.set(url);
    this.loading.set(false);
  }

  openProduct(product: Product) {
    this.activeProduct.set(product);
  }

  toggleStar(toggled: Product) {
    this.products.update((items) =>
      items.map((p) =>
        p === toggled ? { ...p, starred: !(p.starred ?? false) } : p,
      ),
    );

    if (this.activeProduct()) {
      const updated = this.products().find((p) => p.id === toggled.id);
      if (updated) this.activeProduct.set(updated);
    }
  }

  closeOverlay() {
    this.activeProduct.set(null);
    this.exportUrl.set(null);
  }

  get hasOverlay(): boolean {
    return (
      Boolean(this.activeProduct()) ||
      this.loading() ||
      Boolean(this.exportUrl())
    );
  }
}
