import {
  Component,
  signal,
  computed,
  input
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { ProductCanvasComponent } from '../canvas/canvas';

@Component({
  selector: 'app-product-gallery',
  standalone: true,
  imports: [CommonModule, ProductCanvasComponent],
  templateUrl: './gallery.html',
  styleUrl: './gallery.scss',
})
export class ProductGalleryComponent {
  readonly imageUrls = input.required<string[]>();

  selectedIndex = signal(0);
  transforms = signal<DOMMatrix[]>([]);

  readonly selectedUrl = computed(() =>
    this.imageUrls()[this.selectedIndex()]
  );

  readonly selectedTransform = computed(() =>
    this.transforms()[this.selectedIndex()] ?? new DOMMatrix()
  );

  ngOnInit() {
    this.transforms.set(
      Array(this.imageUrls().length).fill(null).map(() => new DOMMatrix())
    );
  }

  updateTransform(matrix: DOMMatrix) {
    const all = [...this.transforms()];
    all[this.selectedIndex()] = matrix;
    this.transforms.set(all);
  }

  select(index: number) {
    this.selectedIndex.set(index);
  }
}
