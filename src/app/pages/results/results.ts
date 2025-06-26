import { Component, computed, input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ResultsThresholdsComponent } from '../../components/results/thresholds/thresholds';
import { ResultsGridComponent } from '../../components/results/grid/grid';
import { ResultsReferenceComponent } from '../../components/results/reference/reference';
import { Thresholds } from '../../models/thresholds';
import { Product } from '../../models/product';
import { exampleProducts } from '../../models/demo-product';

@Component({
  selector: 'app-results',
  standalone: true,
  imports: [
    CommonModule,
    ResultsThresholdsComponent,
    ResultsGridComponent,
    ResultsReferenceComponent,
  ],
  templateUrl: './results.html',
  styleUrls: ['./results.scss'],
})
export class ResultsPage {
  readonly reference = input<Product>();
  readonly exampleProducts = exampleProducts;

  readonly target = computed(() => this.reference() ?? this.exampleProducts[0]);

  handleApply(thresholds: Thresholds) {
    console.log('Thresholds received:', thresholds);
  }
}
