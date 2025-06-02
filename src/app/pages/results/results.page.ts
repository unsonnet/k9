// src/app/results/results.component.ts
import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Product } from '../../models/product.model';
import { ProductCellComponent } from '../../components/product/cell/cell.component';
import { SurveyResponse } from '../../models/survey.model';
import { ProductPage } from '../product/product.page';

@Component({
  selector: 'app-results',
  standalone: true,
  imports: [CommonModule, ProductCellComponent, ProductPage],
  templateUrl: './results.page.html',
  styleUrls: ['./results.page.scss'],
})
export class ResultsPage {
  @Input() products: Product[] = [];
  @Input() reference: string[] = [];
  @Output() productSelected = new EventEmitter<Product>();

  selectedProduct: Product | null = null;
  surveyResponses: { [productId: string]: SurveyResponse } = {};

  onProductClick(product: Product) {
    this.productSelected.emit(product);
    this.selectedProduct = product;
  }
}
