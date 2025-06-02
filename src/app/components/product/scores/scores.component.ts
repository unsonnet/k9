// src/app/product-scores/product-scores.component.ts
import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Scores } from '../../../models/product.model';

@Component({
  selector: 'app-product-scores',
  standalone: true,
  imports: [CommonModule],
  templateUrl: `./scores.component.html`,
  styleUrl: './scores.component.scss',
})
export class ProductScoresComponent {
  @Input() scores!: Scores;

  @Input() ix!: number;
  @Input() jx!: number;

  getCategories(): string[] {
    return Object.keys(this.scores || {});
  }

  getMetrics(category: string): string[] {
    return Object.keys(this.scores[category] || {});
  }

  getMetricValue(category: string, metric: string): number | null {
    const grid = this.scores[category]?.[metric];
    if (!grid || this.ix >= grid.length || this.jx >= grid[this.ix].length) {
      return null;
    }
    const score = grid[this.ix][this.jx];
    return score == null ? null : 1 - score;
  }

  titleCase(input: string): string {
    return input
      .replace(/[-_]/g, ' ')
      .replace(/\w\S*/g, (w) => w[0].toUpperCase() + w.slice(1).toLowerCase());
  }
}
