import {
  Component,
  Input,
  Output,
  EventEmitter,
  ViewChild,
  ElementRef,
  AfterViewInit,
  OnChanges,
  SimpleChanges,
} from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-product-gallery',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './gallery.component.html',
  styleUrl: './gallery.component.scss',
})
export class ProductGalleryComponent implements AfterViewInit, OnChanges {
  @Input() urls: string[] = [];

  @Output() selectedIndexChange = new EventEmitter<number>();

  @ViewChild('imageContainer') imageContainerRef!: ElementRef<HTMLDivElement>;
  @ViewChild('mainImage') mainImageRef!: ElementRef<HTMLImageElement>;

  selectedImage: string | null = null;
  selectedIndex: number = -1;

  rotations: Record<string, number> = {};
  scales: Record<string, number> = {};
  pans: Record<string, { x: number; y: number }> = {};

  isPanning = false;
  panStart = { x: 0, y: 0 };

  ngAfterViewInit() {
    if (this.urls.length && !this.selectedImage) {
      setTimeout(() => this.selectImage(this.urls[0]));
    }
  }

  ngOnChanges(changes: SimpleChanges) {
    if (changes['urls']) {
      const newUrls: string[] = changes['urls'].currentValue;
      if (newUrls?.length) {
        this.selectImage(newUrls[0]);
      } else {
        this.selectedImage = null;
        this.selectedIndex = -1;
      }
    }
  }

  selectImage(url: string) {
    if (!url) return;

    this.selectedImage = url;
    this.selectedIndex = this.urls.indexOf(url);
    this.selectedIndexChange.emit(this.selectedIndex);

    this.rotations[url] ??= 0;
    this.scales[url] ??= 1;
  }

  onImageLoad() {
    if (!this.selectedImage || this.pans[this.selectedImage]) return;

    const imgEl = this.mainImageRef?.nativeElement;
    const containerEl = this.imageContainerRef?.nativeElement;
    if (!imgEl || !containerEl) return;

    const scale = this.scales[this.selectedImage] ?? 1;

    const imgRect = imgEl.getBoundingClientRect();
    const imgWidth = imgRect.width / scale;
    const imgHeight = imgRect.height / scale;

    // Set pan only if it's not already set (first time load only)
    this.pans[this.selectedImage] = {
      x: -imgWidth / 2,
      y: -imgHeight / 2,
    };
  }

  rotate(degrees: number) {
    if (!this.selectedImage) return;
    this.rotations[this.selectedImage] =
      (this.rotations[this.selectedImage] + degrees) % 360;
  }

  getTransform(url: string): string {
    const rotation = this.rotations[url] || 0;
    const scale = this.scales[url] || 1;
    const pan = this.pans[url] || { x: 0, y: 0 };

    return `
      rotate(${rotation}deg)
      scale(${scale})
      translate(${pan.x}px, ${pan.y}px)
    `;
  }

  getOuterTransform(): string {
    if (!this.selectedImage) return '';
    const rotation = this.rotations[this.selectedImage] ?? 0;
    const scale = this.scales[this.selectedImage] ?? 1;
    return `rotate(${rotation}deg) scale(${scale})`;
  }

  getInnerTransform(): string {
    if (!this.selectedImage) return '';
    const pan = this.pans[this.selectedImage] ?? { x: 0, y: 0 };
    return `translate(${pan.x}px, ${pan.y}px)`;
  }

  startPan(event: MouseEvent) {
    if (!this.selectedImage) return;
    this.isPanning = true;
    this.panStart = { x: event.clientX, y: event.clientY };
    event.preventDefault();
  }

  onPan(event: MouseEvent) {
    if (!this.isPanning || !this.selectedImage) return;

    const dx = event.clientX - this.panStart.x;
    const dy = event.clientY - this.panStart.y;
    this.panStart = { x: event.clientX, y: event.clientY };

    const scale = this.scales[this.selectedImage] ?? 1;
    const rotation = this.rotations[this.selectedImage] ?? 0;

    const radians = (-rotation * Math.PI) / 180;
    const cos = Math.cos(radians);
    const sin = Math.sin(radians);
    const rotatedDx = dx * cos - dy * sin;
    const rotatedDy = dx * sin + dy * cos;

    const current = this.pans[this.selectedImage]!;
    this.pans[this.selectedImage] = {
      x: current.x + rotatedDx / scale,
      y: current.y + rotatedDy / scale,
    };
  }

  endPan() {
    this.isPanning = false;
  }

  onZoom(event: WheelEvent) {
    if (!this.selectedImage) return;
    const delta = event.deltaY < 0 ? 0.1 : -0.1;
    const newScale = Math.max(
      0.1,
      (this.scales[this.selectedImage] || 1) + delta,
    );
    this.scales[this.selectedImage] = newScale;
    event.preventDefault();

    // recenter if user zooms while holding Shift
    if (event.shiftKey) {
      this.onImageLoad();
    }
  }
}
