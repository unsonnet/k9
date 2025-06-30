import { Component, computed, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatButtonModule } from '@angular/material/button';
import { Router } from '@angular/router';
import { firstValueFrom } from 'rxjs';

import { ResultsThresholdsComponent } from '../../components/results/thresholds/thresholds';
import { ResultsGridComponent } from '../../components/results/grid/grid';
import { ResultsReferenceComponent } from '../../components/results/reference/reference';
import { ProductPage } from '../product/product';

import { Product } from '../../models/product';
import { Thresholds } from '../../models/thresholds';
import { Reference } from '../../models/reference';
import { Export } from '../../services/export';
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
  // === Injected Services ===
  private readonly fetch = inject(Fetch);
  private readonly exportService = inject(Export);

  // === Initial State from Router ===
  readonly reference = signal<Reference<string>>({
    type: '',
    material: '',
    length: null,
    width: null,
    thickness: null,
    images: [],
  });

  readonly job = signal<string>('');

  constructor() {
    const state = inject(Router).getCurrentNavigation()?.extras.state as
      | { reference: Reference<string>; job: string }
      | undefined;

    if (!state?.reference || !state?.job) {
      throw new Error('Results page loaded without reference or job');
    }

    this.reference.set(state.reference);
    this.job.set(state.job);
  }

  // === UI State ===
  readonly products = signal<Product[]>([]);
  readonly orderBy = signal<'score' | 'name' | 'starred'>('score');
  readonly activeProduct = signal<Product | null>(null);

  // === Overlay State ===
  readonly loadingMessage = signal<string | null>(null);
  readonly exportUrl = signal<string | null>(null);
  readonly overlayError = signal<string | null>(null);

  // === Computed Signals ===
  readonly sortedProducts = computed(() => {
    const products = [...this.products()];
    switch (this.orderBy()) {
      case 'name':
        return products.sort((a, b) =>
          a.description.name.localeCompare(b.description.name),
        );
      case 'starred':
        return products.sort(
          (a, b) => Number(b.starred ?? false) - Number(a.starred ?? false),
        );
      default:
        return products;
    }
  });

  readonly starredCount = computed(
    () => this.sortedProducts().filter((p) => p.starred).length,
  );

  readonly exportEnabled = computed(() =>
    this.sortedProducts().some((p) => p.starred),
  );

  get hasOverlay(): boolean {
    return (
      !!this.activeProduct() ||
      !!this.loadingMessage() ||
      !!this.exportUrl() ||
      !!this.overlayError()
    );
  }

  // === Actions ===

  async handleFilter(thresholds: Thresholds) {
    this.loadingMessage.set('Filtering products...');
    this.overlayError.set(null);

    try {
      const response = await firstValueFrom(
        this.fetch.filter(this.job(), thresholds, 0),
      );

      if (response.status !== 200 || !response.body) {
        throw new Error(response.error ?? `Status ${response.status}`);
      }

      this.products.set(response.body);
    } catch (err) {
      console.error(err);
      this.overlayError.set(
        err instanceof Error ? err.message : 'Filtering failed.',
      );
    } finally {
      this.loadingMessage.set(null);
    }
  }

  async handleExport() {
    const starred = this.products().filter((p) => p.starred);
    if (starred.length === 0) return;

    this.loadingMessage.set('Packaging products...');
    this.exportUrl.set(null);
    this.overlayError.set(null);

    try {
      const blob = await this.exportService.exportProducts(
        this.reference(),
        starred,
      );
      this.exportUrl.set(URL.createObjectURL(blob));
    } catch (err) {
      console.error(err);
      this.overlayError.set(
        err instanceof Error ? err.message : 'Export failed.',
      );
    } finally {
      this.loadingMessage.set(null);
    }
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
    this.overlayError.set(null);
    this.loadingMessage.set(null);
  }
}
