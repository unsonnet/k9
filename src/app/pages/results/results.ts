import { Component, computed, input, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ResultsThresholdsComponent } from '../../components/results/thresholds/thresholds';
import { ResultsGridComponent } from '../../components/results/grid/grid';
import { ResultsReferenceComponent } from '../../components/results/reference/reference';
import { Thresholds } from '../../models/thresholds';
import { Product } from '../../models/product';
import { exampleProducts } from '../../models/demo-product';
import { ProductPage } from '../product/product';

@Component({
  selector: 'app-results',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    ResultsThresholdsComponent,
    ResultsGridComponent,
    ResultsReferenceComponent,
    ProductPage,
  ],
  templateUrl: './results.html',
  styleUrls: ['./results.scss'],
})
export class ResultsPage {
  readonly reference = input<Product>();
  readonly target = computed(() => this.reference() ?? this.products()[0]);

  readonly products = signal<Product[]>(exampleProducts);
  readonly orderBy = signal<'score' | 'name' | 'starred'>('score');
  readonly activeProduct = signal<Product | null>(null);

  readonly thresholdsDisabled = signal(false);
  readonly exportEnabled = computed(() =>
    this.sortedProducts().some((p) => p.starred),
  );

  readonly sortedProducts = computed(() => {
    const products = [...this.products()];
    const key = this.orderBy();

    return products.sort((a, b) => {
      if (key === 'score') return 0;
      if (key === 'name') return a.name.localeCompare(b.name);
      if (key === 'starred') {
        return Number(b.starred ?? false) - Number(a.starred ?? false);
      }
      return 0;
    });
  });


  handleApply(thresholds: Thresholds) {
    this.thresholdsDisabled.set(true);
    console.log('Thresholds received:', thresholds);
    setTimeout(() => {
      this.thresholdsDisabled.set(false);
    }, 3000);
  }

  openProduct(product: Product) {
    this.activeProduct.set(product);
  }

  toggleStar(toggled: Product) {
    this.products.update((items) =>
      items.map((p) =>
        p === toggled ? { ...p, starred: !(p.starred ?? false) } : p
      )
    );
  }

  closeOverlay() {
    this.activeProduct.set(null);
  }
}
