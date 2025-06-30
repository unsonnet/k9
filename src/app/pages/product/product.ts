import { Component, computed, signal, input, output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import { Product } from '../../models/product';
import { ProductDescriptionComponent } from '../../components/product/description/description';
import { ProductGalleryComponent } from '../../components/product/gallery/gallery';
import { Reference } from '../../models/reference';

@Component({
  selector: 'app-product',
  standalone: true,
  imports: [
    CommonModule,
    MatIconModule,
    ProductDescriptionComponent,
    ProductGalleryComponent,
  ],
  templateUrl: './product.html',
  styleUrl: './product.scss',
})
export class ProductPage {
  readonly product = input.required<Product>();
  readonly reference = input.required<Reference<string>>();
  readonly starToggled = output<void>();

  get colorKeys() {
    return Object.keys(this.product().scores.product.color);
  }

  get patternKeys() {
    return Object.keys(this.product().scores.product.pattern);
  }

  toggleStar(event: MouseEvent) {
    event.stopPropagation();
    this.starToggled.emit();
  }

  readonly galleryProduct = computed(() => this.product().images);
  readonly galleryReference = computed(() => this.reference().images);
}
