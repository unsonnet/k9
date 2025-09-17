import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import { Product } from '../../../models/product';
import { ProductMetricsComponent } from '../metrics/metrics';

@Component({
  selector: 'app-product-description',
  standalone: true,
  imports: [CommonModule, MatIconModule, ProductMetricsComponent],
  templateUrl: './description.html',
  styleUrl: './description.scss',
})
export class ProductDescriptionComponent {
  @Input({ required: true }) product!: Product;
  @Output() starToggled = new EventEmitter<void>();

  get lengthInInches(): string {
    const length = this.product?.description?.length;
    return length != null ? Math.trunc(length / 2.54).toString() : '';
  }

  get widthInInches(): string {
    const width = this.product?.description?.width;
    return width != null ? Math.trunc(width / 2.54).toString() : '';
  }

  toggleStar(event: MouseEvent) {
    event.stopPropagation();
    this.starToggled.emit();
  }
}
