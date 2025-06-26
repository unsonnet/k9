import { Component, input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Product } from '../../../models/product';

@Component({
  selector: 'app-product-description',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './description.html',
  styleUrl: './description.scss'
})
export class ProductDescriptionComponent {
  readonly product = input.required<Product>();

  get colorKeys() {
    return Object.keys(this.product().scores.product.color);
  }

  get patternKeys() {
    return Object.keys(this.product().scores.product.pattern);
  }
}
