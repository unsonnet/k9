import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Product } from '../../../models/product';

@Component({
  selector: 'app-product-metrics',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './metrics.html',
  styleUrl: './metrics.scss',
})
export class ProductMetricsComponent {
  @Input({ required: true }) product!: Product;

  readonly productSections: (keyof Product['scores'])[] = [
    'color',
    'pattern',
  ];

  metricKeys(section: Record<string, number>): string[] {
    return Object.keys(section);
  }

  truncate(value: number): number {
    return Math.floor(value);
  }
}
