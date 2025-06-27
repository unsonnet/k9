import { Component, input, output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Product } from '../../models/product';
import { ProductDescriptionComponent } from '../../components/product/description/description';
import { ProductGalleryComponent } from '../../components/product/gallery/gallery';

@Component({
  selector: 'app-product',
  standalone: true,
  imports: [CommonModule, ProductDescriptionComponent, ProductGalleryComponent],
  templateUrl: './product.html',
  styleUrl: './product.scss',
})
export class ProductPage {
  readonly product = input.required<Product>();
  readonly reference = input.required<Product>();
  readonly starToggled = output<void>();
}
