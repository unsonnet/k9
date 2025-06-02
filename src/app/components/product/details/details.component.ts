// src/app/product-details/product-details.component.ts
import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Product } from '../../../models/product.model';

@Component({
  selector: 'app-product-details',
  standalone: true,
  imports: [CommonModule],
  templateUrl: `./details.component.html`,
  styleUrl: `./details.component.scss`,
})
export class ProductDetailsComponent {
  @Input() product!: Product;

  filteredDetails() {
    return Object.entries(this.product?.details ?? {})
      .filter(([_, value]) => value !== null)
      .map(([key, value]) => ({ key, value }));
  }

  titleCase(key: string): string {
    return key
      .replace(/[-_]/g, ' ')
      .replace(/\w\S*/g, (w) => w[0].toUpperCase() + w.slice(1).toLowerCase());
  }
}
