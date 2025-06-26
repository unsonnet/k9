import { Component, input, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Product } from '../../../models/product';

@Component({
  selector: 'app-results-reference',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './reference.html',
  styleUrl: './reference.scss',
})
export class ResultsReferenceComponent {
  readonly reference = input.required<Product>();
  currentImageIndex = signal(0);

  nextImage() {
    if (this.currentImageIndex() < this.reference().images.length - 1) {
      this.currentImageIndex.update((i) => i + 1);
    }
  }

  prevImage() {
    if (this.currentImageIndex() > 0) {
      this.currentImageIndex.update((i) => i - 1);
    }
  }
}
