import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import { Product } from '../../../models/product';

type ProductSectionName = keyof Product['scores']['product']; // 'shape' | 'color' | 'pattern'
type ImageSectionName = keyof Product['scores']['image']; // 'color' | 'pattern' | 'variation'

@Component({
  selector: 'app-product-description',
  standalone: true,
  imports: [CommonModule, MatIconModule],
  templateUrl: './description.html',
  styleUrl: './description.scss',
})
export class ProductDescriptionComponent {
  @Input({ required: true }) product!: Product;
  @Output() starToggled = new EventEmitter<void>();

  toggleStar(event: MouseEvent) {
    event.stopPropagation();
    this.starToggled.emit();
  }

  readonly productSections: ProductSectionName[] = [
    'shape',
    'color',
    'pattern',
  ];
  readonly imageSections: ImageSectionName[] = [
    'color',
    'pattern',
    'variation',
  ];

  metricKeys(section: Record<string, number>): string[] {
    return Object.keys(section);
  }
}
