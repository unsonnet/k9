import {
  Component,
  ElementRef,
  ViewChild,
  AfterViewInit,
  OnChanges,
  SimpleChanges,
  input,
  output,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';

@Component({
  selector: 'app-product-canvas',
  standalone: true,
  imports: [CommonModule, MatIconModule],
  templateUrl: './canvas.html',
  styleUrl: './canvas.scss',
})
export class ProductCanvasComponent implements AfterViewInit, OnChanges {
  readonly imageUrl = input.required<string>();
  readonly initialTransform = input<DOMMatrix | undefined>();
  readonly transformChanged = output<DOMMatrix>();

  @ViewChild('canvas', { static: true })
  private canvasRef!: ElementRef<HTMLCanvasElement>;

  mode: 'translate' | 'rotate' = 'translate';

  private isDragging = false;
  private startX = 0;
  private startY = 0;
  private deltaRotation = 0;
  private cumulativeRotation = 0;

  private baseMatrix = new DOMMatrix();
  private currentMatrix = new DOMMatrix();
  private loadedImage: HTMLImageElement | null = null;

  ngAfterViewInit() {
    this.loadImage();
  }

  ngOnChanges(changes: SimpleChanges) {
    if (changes['imageUrl']) {
      this.loadImage();
    } else if (changes['initialTransform'] && this.loadedImage) {
      this.currentMatrix = this.initialTransform() ?? this.defaultTransform();
      this.drawImage();
    }
  }

  private loadImage() {
    const img = new Image();
    img.src = this.imageUrl();
    img.onload = () => {
      this.loadedImage = img;
      this.syncCanvasSize();
      this.currentMatrix = this.initialTransform() ?? this.defaultTransform();
      this.drawImage();
      this.transformChanged.emit(this.currentMatrix);
    };
  }

  private syncCanvasSize() {
    const canvas = this.canvasRef.nativeElement;
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width;
    canvas.height = rect.height;
  }

  private defaultTransform(): DOMMatrix {
    if (!this.loadedImage) return new DOMMatrix();
    const canvas = this.canvasRef.nativeElement;
    const scale = Math.min(
      canvas.width / this.loadedImage.naturalWidth,
      canvas.height / this.loadedImage.naturalHeight,
    );
    return new DOMMatrix().scale(scale / 1.5);
  }

  private drawImage() {
    if (!this.loadedImage) return;
    const canvas = this.canvasRef.nativeElement;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const cx = canvas.width / 2;
    const cy = canvas.height / 2;
    ctx.save();
    ctx.translate(cx, cy);
    ctx.transform(
      this.currentMatrix.a,
      this.currentMatrix.b,
      this.currentMatrix.c,
      this.currentMatrix.d,
      this.currentMatrix.e,
      this.currentMatrix.f,
    );

    ctx.drawImage(
      this.loadedImage,
      -this.loadedImage.naturalWidth / 2,
      -this.loadedImage.naturalHeight / 2,
    );

    ctx.strokeStyle = 'white';
    const scaleX = Math.hypot(this.currentMatrix.a, this.currentMatrix.b);
    const scaleY = Math.hypot(this.currentMatrix.c, this.currentMatrix.d);
    ctx.lineWidth = 2 / ((scaleX + scaleY) / 2);
    ctx.strokeRect(
      -this.loadedImage.naturalWidth / 2,
      -this.loadedImage.naturalHeight / 2,
      this.loadedImage.naturalWidth,
      this.loadedImage.naturalHeight,
    );

    ctx.restore();
  }

  setMode(mode: 'translate' | 'rotate') {
    this.mode = mode;
  }

  resetView() {
    if (!this.loadedImage) return;
    this.currentMatrix = this.defaultTransform();
    this.drawImage();
    this.transformChanged.emit(this.currentMatrix);
  }

  onMouseDown(event: MouseEvent) {
    this.isDragging = true;
    this.startX = event.offsetX;
    this.startY = event.offsetY;
    this.baseMatrix = this.currentMatrix;
    this.deltaRotation = 0;
  }

  onMouseMove(event: MouseEvent) {
    if (!this.isDragging) return;

    const delta = new DOMMatrix();
    if (this.mode === 'translate') {
      delta.translateSelf(
        event.offsetX - this.startX,
        event.offsetY - this.startY,
      );
    } else {
      const canvas = this.canvasRef.nativeElement;
      const cx = canvas.width / 2;
      const cy = canvas.height / 2;

      const a1 = Math.atan2(this.startY - cy, this.startX - cx);
      const a2 = Math.atan2(event.offsetY - cy, event.offsetX - cx);
      this.deltaRotation = ((a2 - a1) * 180) / Math.PI;

      if (event.shiftKey) {
        const total = this.cumulativeRotation + this.deltaRotation;
        const snapped = Math.round(total / 45) * 45;
        this.deltaRotation += snapped - total;
      }

      delta.rotateSelf(this.deltaRotation);
    }

    this.currentMatrix = delta.multiply(this.baseMatrix);
    this.drawImage();
  }

  onMouseUp() {
    if (!this.isDragging) return;
    this.isDragging = false;
    this.cumulativeRotation =
      (this.cumulativeRotation + this.deltaRotation) % 360;
    this.transformChanged.emit(this.currentMatrix);
  }

  onWheel(event: WheelEvent) {
    event.preventDefault();
    const canvas = this.canvasRef.nativeElement;
    const rect = canvas.getBoundingClientRect();
    const cx = canvas.width / 2;
    const cy = canvas.height / 2;
    const mx = event.clientX - rect.left;
    const my = event.clientY - rect.top;
    const zoom = event.deltaY < 0 ? 1.1 : 0.9;

    const delta = new DOMMatrix()
      .translate(mx - cx, my - cy)
      .scale(zoom)
      .translate(-(mx - cx), -(my - cy));

    this.currentMatrix = delta.multiply(this.currentMatrix);
    this.drawImage();
    this.transformChanged.emit(this.currentMatrix);
  }
}
