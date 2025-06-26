import {
  Component,
  ElementRef,
  ViewChild,
  HostListener,
  input,
  output,
  SimpleChanges,
} from '@angular/core';
import { MatIconModule } from '@angular/material/icon';

@Component({
  selector: 'app-product-canvas',
  standalone: true,
  imports: [MatIconModule],
  templateUrl: './canvas.html',
  styleUrl: './canvas.scss',
})
export class ProductCanvasComponent {
  readonly imageUrl = input.required<string>();
  readonly transform = input<DOMMatrix>(new DOMMatrix());
  readonly transformChanged = output<DOMMatrix>();

  @ViewChild('canvas', { static: true })
  canvasRef!: ElementRef<HTMLCanvasElement>;

  mode: 'translate' | 'rotate' = 'translate';
  isDragging = false;
  startX = 0;
  startY = 0;
  currentMatrix = new DOMMatrix();

  ngAfterViewInit() {
    this.currentMatrix = this.transform();
    this.drawImage();
  }

  ngOnChanges(changes: SimpleChanges) {
    if (changes['imageUrl'] || changes['transform']) {
      this.currentMatrix = this.transform();
      this.drawImage();
    }
  }

  drawImage() {
    const canvas = this.canvasRef.nativeElement;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const img = new Image();
    img.src = this.imageUrl();
    img.onload = () => {
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

      const iw = img.width;
      const ih = img.height;
      ctx.drawImage(img, -iw / 2, -ih / 2);

      ctx.strokeStyle = 'white';
      const scaleX = Math.hypot(this.currentMatrix.a, this.currentMatrix.b);
      const scaleY = Math.hypot(this.currentMatrix.c, this.currentMatrix.d);
      const effectiveScale = (scaleX + scaleY) / 2;
      ctx.lineWidth = 2 / effectiveScale;
      ctx.strokeRect(-iw / 2, -ih / 2, iw, ih);

      ctx.restore();
    };
  }

  setMode(mode: 'translate' | 'rotate') {
    this.mode = mode;
  }

  @HostListener('mousedown', ['$event'])
  onMouseDown(event: MouseEvent) {
    this.isDragging = true;
    this.startX = event.offsetX;
    this.startY = event.offsetY;
  }

  @HostListener('mousemove', ['$event'])
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
    } else if (this.mode === 'rotate') {
      const angle1 = Math.atan2(this.startY - cy, this.startX - cx);
      const angle2 = Math.atan2(event.offsetY - cy, event.offsetX - cx);
      const deltaAngle = angle2 - angle1;
      delta.rotateSelf((deltaAngle * 180) / Math.PI);
    }

    this.currentMatrix = delta.multiply(this.currentMatrix);
    this.startX = event.offsetX;
    this.startY = event.offsetY;
    this.drawImage();
  }

  @HostListener('mouseup')
  @HostListener('mouseleave')
  onMouseUp() {
    if (this.isDragging) {
      this.isDragging = false;
      this.emitTransform();
    }
  }

  @HostListener('wheel', ['$event'])
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
    this.emitTransform();
  }

  resetTransform() {
    this.currentMatrix = new DOMMatrix();
    this.drawImage();
    this.emitTransform();
  }

  private emitTransform() {
    this.transformChanged.emit(this.currentMatrix);
  }
}
