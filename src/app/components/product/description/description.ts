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

  toggleStar(event: MouseEvent) {
    event.stopPropagation();
    this.starToggled.emit();
  }
}
