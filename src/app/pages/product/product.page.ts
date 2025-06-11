import { Component, Input, Output, EventEmitter, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Product, Scores } from '../../models/product.model';
import { SurveyResponse } from '../../models/survey.model';
import { ProductDetailsComponent } from '../../components/product/details/details.component';
import { ProductScoresComponent } from '../../components/product/scores/scores.component';
import { ProductGalleryComponent } from '../../components/product/gallery/gallery.component';
import { ProductSurveyComponent } from '../../components/product/survey/survey.component';

@Component({
  selector: 'app-product',
  standalone: true,
  imports: [
    CommonModule,
    ProductDetailsComponent,
    ProductScoresComponent,
    ProductSurveyComponent,
    ProductGalleryComponent,
  ],
  templateUrl: `./product.page.html`,
  styleUrls: ['./product.page.scss'],
})
export class ProductPage {
  @Input({ required: true }) product!: Product;
  @Input({ required: true }) reference!: File[];
  @Input() surveyValue: SurveyResponse | null = null;
  @Output() surveyValueChange = new EventEmitter<SurveyResponse>();

  selectedIx = signal(0);
  selectedJx = signal(0);

  referenceUrls: string[] = [];

  ngOnChanges() {
    if (this.reference?.length) {
      // Update blob URL list based on new reference input
      this.referenceUrls = this.reference.map((file) =>
        URL.createObjectURL(file),
      );
    }
  }

  onSurveyChange(value: SurveyResponse) {
    this.surveyValueChange.emit(value);
  }

  // Reduce each 2D array in scores to a single min value per metric
  reducedScores(): Scores {
    const result: Scores = {};
    for (const category in this.product.scores) {
      result[category] = {};
      for (const metric in this.product.scores[category]) {
        const matrix = this.product.scores[category][metric];
        const flat = matrix.flat().filter((v): v is number => v !== null);
        const min = flat.length > 0 ? Math.min(...flat) : null;
        result[category][metric] = [[min]];
      }
    }
    return result;
  }
}
