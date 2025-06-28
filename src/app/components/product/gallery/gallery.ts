import {
  Component,
  Input,
  Signal,
  signal,
  computed,
  ChangeDetectionStrategy,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { ProductCanvasComponent } from '../canvas/canvas';
import { ProductThumbnailsComponent } from '../thumbnails/thumbnails';

@Component({
  selector: 'app-product-gallery',
  standalone: true,
  imports: [CommonModule, ProductCanvasComponent, ProductThumbnailsComponent],
  templateUrl: './gallery.html',
  styleUrl: './gallery.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ProductGalleryComponent {
  @Input({ required: true }) imageUrls!: Signal<string[]>;

  readonly selectedIndex = signal(0);
  private readonly transforms = signal<DOMMatrix[]>([]);

  readonly selectedUrl = computed(() => this.imageUrls()[this.selectedIndex()]);
  readonly selectedTransform = computed(
    () => this.transforms()[this.selectedIndex()],
  );

  readonly select = (i: number) => {
    this.selectedIndex.set(i);
  };

  readonly updateTransform = (matrix: DOMMatrix) => {
    const all = [...this.transforms()];
    all[this.selectedIndex()] = matrix;
    this.transforms.set(all);
  };
}
