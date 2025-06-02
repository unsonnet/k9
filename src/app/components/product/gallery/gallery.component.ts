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

  // Emit the index of the selected image
  @Output() selectedIndexChange = new EventEmitter<number>();

  @ViewChild('imageContainer') imageContainerRef!: ElementRef<HTMLDivElement>;

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
    this.selectedImage = url;
    this.selectedIndex = this.urls.indexOf(url);
    this.selectedIndexChange.emit(this.selectedIndex); // Emit selected index

    this.rotations[url] ??= 0;
    this.scales[url] ??= 1;
    this.pans[url] ??= { x: 0, y: 0 };
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
      translate(-50%, -50%)
      translate(${pan.x}px, ${pan.y}px)
      rotate(${rotation}deg)
      scale(${scale})
    `;
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
    const current = this.pans[this.selectedImage]!;
    this.pans[this.selectedImage] = {
      x: current.x + dx,
      y: current.y + dy,
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
  }
}
