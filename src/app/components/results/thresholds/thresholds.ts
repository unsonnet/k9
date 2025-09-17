import { Component, input, output } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatSliderModule } from '@angular/material/slider';
import { MatButtonModule } from '@angular/material/button';
import { CommonModule } from '@angular/common';
import { Thresholds } from '../../../models/thresholds';

@Component({
  selector: 'app-results-thresholds',
  standalone: true,
  imports: [CommonModule, FormsModule, MatSliderModule, MatButtonModule],
  templateUrl: './thresholds.html',
  styleUrl: './thresholds.scss',
})
export class ResultsThresholdsComponent {
  readonly applyFilter = output<Thresholds>();
  readonly exportResults = output<void>();
  readonly exportEnabled = input(true);

  product = {
    type_: {
      type: 0.5,
      material: 0.5,
    } as Record<string, number>,
    shape: {
      length: 1.5,
      width: 1.5,
    } as Record<string, number>,
    color: {
      primary: 50,
      secondary: 50,
      tertiary: 50,
    } as Record<string, number>,
    pattern: {
      primary: 50,
      secondary: 50,
      tertiary: 50,
    } as Record<string, number>,
  };

  readonly productShapeFields = Object.keys(this.product.shape);
  readonly productColorFields = Object.keys(this.product.color);
  readonly productPatternFields = Object.keys(this.product.pattern);

  onFilter(): void {
    const toRange = (v: number, iv: boolean) => (iv ? (100 - v) / 100 : v);

    const buildSection = (
      source: Record<string, number>,
      invert: boolean = true,
    ): Record<string, number> =>
      Object.fromEntries(
        Object.keys(source).map((key) => [key, toRange(source[key], invert)]),
      );

    const thresholds: Thresholds = {
      type_: {
        missing: false as any,
        ...buildSection(this.product.type_, false),
      },
      shape: {
        missing: true as any,
        ...buildSection(this.product.shape, false),
      },
      color: {
        missing: false as any,
        ...buildSection(this.product.color),
      },
      pattern: {
        missing: false as any,
        ...buildSection(this.product.pattern),
      },
    };

    this.applyFilter.emit(thresholds);
  }

  onExport(): void {
    this.exportResults.emit();
  }
}
