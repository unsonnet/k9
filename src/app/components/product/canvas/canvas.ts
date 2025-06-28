import {
  Component,
  ElementRef,
  Input,
  Output,
  ViewChild,
  AfterViewInit,
  OnChanges,
  SimpleChanges,
  EventEmitter,
} from '@angular/core';
import { MatIconModule } from '@angular/material/icon';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-product-canvas',
  standalone: true,
  imports: [CommonModule, MatIconModule],
  templateUrl: './canvas.html',
  styleUrl: './canvas.scss',
})
export class ProductCanvasComponent implements AfterViewInit, OnChanges {
  @Input() imageUrl!: string;
  @Input() initialTransform?: DOMMatrix;
  @Output() transformChanged = new EventEmitter<DOMMatrix>();

  @ViewChild('canvas', { static: true })
  canvasRef!: ElementRef<HTMLCanvasElement>;

  mode: 'translate' | 'rotate' = 'translate';
  isDragging = false;
  startX = 0;
  startY = 0;
  currentMatrix = new DOMMatrix();
  loadedImage: HTMLImageElement | null = null;

  ngAfterViewInit() {
    this.loadImage();
  }

  ngOnChanges(changes: SimpleChanges) {
    if (changes['imageUrl']) {
      this.loadImage();
    } else if (changes['initialTransform'] && this.loadedImage) {
      this.currentMatrix = this.initialTransform ?? this.defaultTransform();
      this.drawImage();
    }
  }

  loadImage() {
    const img = new Image();
    img.src = this.imageUrl;
    img.onload = () => {
      this.loadedImage = img;
      this.syncCanvasSize();
      this.currentMatrix = this.initialTransform ?? this.defaultTransform();
      this.drawImage();
      this.transformChanged.emit(this.currentMatrix);
    };
  }

  defaultTransform(): DOMMatrix {
    if (!this.loadedImage) return new DOMMatrix();
    const canvas = this.canvasRef.nativeElement;
    const scale = Math.min(
      canvas.width / this.loadedImage.naturalWidth,
      canvas.height / this.loadedImage.naturalHeight,
    );
    return new DOMMatrix().scale(scale / 1.5);
  }

  syncCanvasSize() {
    const canvas = this.canvasRef.nativeElement;
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width;
    canvas.height = rect.height;
  }

  drawImage() {
    if (!this.loadedImage) return;
    const canvas = this.canvasRef.nativeElement;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    ctx.save();
    const cx = canvas.width / 2;
    const cy = canvas.height / 2;
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
  }

  onMouseMove(event: MouseEvent) {
    if (!this.isDragging) return;
    const canvas = this.canvasRef.nativeElement;
    const cx = canvas.width / 2;
    const cy = canvas.height / 2;
    const dx = event.offsetX - this.startX;
    const dy = event.offsetY - this.startY;

    const delta = new DOMMatrix();
    if (this.mode === 'translate') {
      delta.translateSelf(dx, dy);
    } else {
      const a1 = Math.atan2(this.startY - cy, this.startX - cx);
      const a2 = Math.atan2(event.offsetY - cy, event.offsetX - cx);
      delta.rotateSelf(((a2 - a1) * 180) / Math.PI);
    }

    this.currentMatrix = delta.multiply(this.currentMatrix);
    this.startX = event.offsetX;
    this.startY = event.offsetY;
    this.drawImage();
  }

  onMouseUp() {
    if (this.isDragging) {
      this.isDragging = false;
      this.transformChanged.emit(this.currentMatrix);
    }
  }

  onWheel(event: WheelEvent) {
    event.preventDefault();
    const canvas = this.canvasRef.nativeElement;
    const rect = canvas.getBoundingClientRect();
    const cx = canvas.width / 2;
    const cy = canvas.height / 2;
    const mouseX = event.clientX - rect.left;
    const mouseY = event.clientY - rect.top;
    const zoom = event.deltaY < 0 ? 1.1 : 0.9;

    const delta = new DOMMatrix()
      .translate(mouseX - cx, mouseY - cy)
      .scale(zoom)
      .translate(-(mouseX - cx), -(mouseY - cy));

    this.currentMatrix = delta.multiply(this.currentMatrix);
    this.drawImage();
    this.transformChanged.emit(this.currentMatrix);
  }
}
