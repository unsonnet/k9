import { Component, signal, input, output } from '@angular/core';
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
  readonly starToggled = output<{ id: string; starred: boolean }>();
  readonly productClicked = output<Product>();

  private starredMap = signal<Record<string, boolean>>({});

  toggleStar(id: string, event: MouseEvent) {
    event.stopPropagation();
    const prev = this.starredMap()[id] ?? false;
    this.starredMap.update((m) => ({ ...m, [id]: !prev }));
    this.starToggled.emit({ id, starred: !prev });
  }

  isStarred(id: string): boolean {
    return this.starredMap()[id] ?? false;
  }

  viewProduct(product: Product) {
    console.log('viewing product', product);
    this.productClicked.emit(product);
  }
}
