import { Component, input, signal } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-results-reference',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './reference.html',
  styleUrl: './reference.scss',
})
export class ResultsReferenceComponent {
  readonly images = input.required<string[]>();
  currentImageIndex = signal(0);

  nextImage() {
    if (this.currentImageIndex() < this.images().length - 1) {
      this.currentImageIndex.update((i) => i + 1);
    }
  }

  prevImage() {
    if (this.currentImageIndex() > 0) {
      this.currentImageIndex.update((i) => i - 1);
    }
  }
}
