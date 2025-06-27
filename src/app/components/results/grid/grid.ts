import { Component, input, output } from '@angular/core';
import { Product } from '../../../models/product';

@Component({
  selector: 'app-results-grid',
  standalone: true,
  templateUrl: './grid.html',
  styleUrls: ['./grid.scss'],
})
export class ResultsGridComponent {
  readonly products = input.required<Product[]>();
  readonly productClicked = output<Product>();

  toggleStar(product: Product, event: MouseEvent) {
    event.stopPropagation();
    product.starred = !(product.starred ?? false);
  }

  viewProduct(product: Product) {
    this.productClicked.emit(product);
  }
}
