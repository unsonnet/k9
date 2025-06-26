import { Component, input, output } from '@angular/core';
import { Product } from '../../../models/product';

@Component({
  selector: 'app-results-grid',
  standalone: true,
  imports: [],
  templateUrl: './grid.html',
  styleUrls: ['./grid.scss'],
})
export class ResultsGridComponent {
  readonly products = input.required<Product[]>();
  readonly starred = input<Record<string, boolean>>();
  readonly starToggled = output<{ id: string; starred: boolean }>();
  readonly productClicked = output<Product>();

  toggleStar(id: string, event: MouseEvent) {
    event.stopPropagation();
    const current = this.starred()?.[id] ?? false;
    this.starToggled.emit({ id, starred: !current });
  }

  isStarred(id: string): boolean {
    return this.starred()?.[id] ?? false;
  }

  viewProduct(product: Product) {
    console.log('viewing product', product);
    this.productClicked.emit(product);
  }
}
