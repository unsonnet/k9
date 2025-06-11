// src/app/results/results.component.ts
import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Product } from '../../models/product.model';
import { ProductCellComponent } from '../../components/product/cell/cell.component';
import { SurveyResponse } from '../../models/survey.model';
import { ProductPage } from '../product/product.page';
import { Router } from '@angular/router';
import { inject } from '@angular/core';
import { Location } from '@angular/common';
import { FilterComponent } from '../../components/filter/filter/filter.component';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import { Thresholds } from '../../models/thresholds.model';
import { API } from '../../../environments/api';
import { Scores } from '../../models/product.model';
import { OnInit } from '@angular/core';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';

@Component({
  selector: 'app-results',
  standalone: true,
  imports: [
    CommonModule,
    ProductCellComponent,
    ProductPage,
    FilterComponent,
    MatProgressSpinnerModule,
  ],
  templateUrl: './results.page.html',
  styleUrls: ['./results.page.scss'],
})
export class ResultsPage {
  @Input() reference: File[] = [];
  @Output() productSelected = new EventEmitter<Product>();
  products: Product[] = [];

  selectedProduct: Product | null = null;
  surveyResponses: { [productId: string]: SurveyResponse } = {};

  isLoading = false;
  errorMessage: string | null = null;

  private job: string = '';
  private readonly http = inject(HttpClient);
  private readonly router = inject(Router);
  private location = inject(Location);

  closeOverlay() {
    this.selectedProduct = null;
  }

  ngOnInit() {
    let state = this.router.getCurrentNavigation()?.extras?.state as {
      products: Product[];
      reference: File[];
      job: string;
    };

    if (!state || !state.products) {
      state = this.location.getState() as typeof state;
    }

    if (state && state.job && state.products && state.reference) {
      this.job = state.job;
      this.products = state.products;
      this.reference = state.reference;
    } else {
      console.warn('No navigation state found.');
    }
  }

  async onThresholdsSubmit(thresholds: Thresholds) {
    if (!this.job) return;
    this.isLoading = true;
    this.errorMessage = null;
    const url = `${API.base}/${this.job}/fetch`;

    try {
      const raw = await firstValueFrom(this.http.post<any[]>(url, thresholds));
      this.products = raw.map((p) => {
        const { id, store, name, images, pattern, color, ...rest } = p;
        const scores: Scores = {};
        if (pattern) scores['pattern'] = pattern;
        if (color) scores['color'] = color;
        return { id, store, name, images, scores, details: rest };
      });
    } catch (e: any) {
      console.error('Fetch failed', e);
      this.errorMessage = `K9 got lost! (${e.status || 'unknown'})`;
    } finally {
      this.isLoading = false;
    }
  }

  closeError() {
    this.errorMessage = null;
  }

  onProductClick(product: Product) {
    this.productSelected.emit(product);
    this.selectedProduct = product;
  }

  onSurveyChange(id: string, survey: SurveyResponse) {
    this.surveyResponses[id] = survey;
  }
}
