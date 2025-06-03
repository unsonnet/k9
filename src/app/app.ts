import { Component } from '@angular/core';
import { QueryComponent } from './components/query/query/query.component';
import { FilterComponent } from './components/filter/filter/filter.component';
import { ResultsPage } from './pages/results/results.page';
import { mockProducts } from './tests/products.data';
import { mockReference } from './tests/reference.data';
import { Product } from './models/product.model';

@Component({
  selector: 'app-root',
  imports: [QueryComponent, FilterComponent, ResultsPage],
  template:
    '<app-query/><app-filter/><app-results [products]="products" [reference]="reference" (productSelected)="viewDetails($event)"/>',
  styleUrl: './app.scss',
})
export class App {
  protected title = 'k9';
  products = mockProducts;
  reference = mockReference;
  viewDetails(product: Product) {
    console.log('Selected product:', product);
    // Navigate or open detail panel
  }
}
