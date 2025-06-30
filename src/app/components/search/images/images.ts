import {
  Component,
  ElementRef,
  HostBinding,
  Optional,
  Self,
  ViewEncapsulation,
  inject,
  signal,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { ControlValueAccessor, NgControl } from '@angular/forms';
import { MatFormFieldControl } from '@angular/material/form-field';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { Subject } from 'rxjs';

interface ImageFile {
  file: File;
  url: string;
}

@Component({
  selector: 'app-search-images',
  standalone: true,
  templateUrl: './images.html',
  styleUrl: './images.scss',
  imports: [CommonModule, MatButtonModule, MatIconModule],
  providers: [
    { provide: MatFormFieldControl, useExisting: SearchImagesComponent },
  ],
  encapsulation: ViewEncapsulation.ShadowDom, // 👈 use Shadow DOM to fully isolate styles and layout
})
export class SearchImagesComponent
  implements ControlValueAccessor, MatFormFieldControl<File[]>
{
  static nextId = 0;

  // -----------------------------
  // Public Reactive State
  // -----------------------------
  files = signal<ImageFile[]>([]);
  dragActive = signal(false);

  // -----------------------------
  // Form Field Control Info
  // -----------------------------
  readonly id = `app-search-images-${SearchImagesComponent.nextId++}`;
  readonly controlType = 'app-search-images';
  readonly stateChanges = new Subject<void>();

  placeholder = ''; // Required by MatFormFieldControl
  errorState = false; // Required by MatFormFieldControl
  focused = false;
  required = false;
  disabled = false;

  hoveredIndex = -1;

  // -----------------------------
  // Dependency Injection
  // -----------------------------
  @Self() @Optional() readonly ngControl: NgControl = inject(NgControl);

  constructor(public elementRef: ElementRef<HTMLElement>) {
    if (this.ngControl) {
      this.ngControl.valueAccessor = this;
    }
  }

  // -----------------------------
  // Value Accessor Methods
  // -----------------------------
  onChange = (_: any) => {};
  onTouched = () => {};

  private wrapFiles(files: File[]): ImageFile[] {
    return files.map((file) => ({
      file,
      url: URL.createObjectURL(file),
    }));
  }

  writeValue(obj: File[] | null): void {
    this.files.set(this.wrapFiles(obj ?? []));
  }

  registerOnChange(fn: any): void {
    this.onChange = fn;
  }

  registerOnTouched(fn: any): void {
    this.onTouched = fn;
  }

  setDisabledState(isDisabled: boolean): void {
    this.disabled = isDisabled;
    this.stateChanges.next();
  }

  // -----------------------------
  // MatFormFieldControl Methods
  // -----------------------------

  get empty(): boolean {
    return this.files().length === 0;
  }

  get shouldLabelFloat(): boolean {
    return this.focused || !this.empty;
  }

  setDescribedByIds(ids: string[]): void {
    // Accessible description support if needed
  }

  onContainerClick(): void {
    this.onTouched();
  }

  get value(): File[] | null {
    return this.files().map((f) => f.file);
  }

  set value(newFiles: File[] | null) {
    const wrapped = this.wrapFiles(newFiles ?? []);
    this.files.set(wrapped);
    this.onChange(wrapped.map((f) => f.file));
    this.stateChanges.next();
  }

  updateErrorState(): void {
    const control = this.ngControl?.control;
    this.errorState = !!control && control.invalid && control.touched;
    this.stateChanges.next();
  }

  // -----------------------------
  // File Event Handlers
  // -----------------------------
  onFileInput(event: Event): void {
    const input = event.target as HTMLInputElement;
    if (input.files?.length) {
      this.value = [...(this.value ?? []), ...input.files];
      this.onTouched();
    }
  }

  removeFile(index: number): void {
    if (this.disabled) return;
    const current = [...this.files()];
    URL.revokeObjectURL(current[index].url);
    current.splice(index, 1);
    this.value = current.map((f) => f.file);
  }

  // -----------------------------
  // Drag-and-Drop Handlers
  // -----------------------------
  onDragOver(event: DragEvent): void {
    event.preventDefault();
    this.dragActive.set(true);
    console.log('on drag over');
  }

  onDrop(event: DragEvent): void {
    event.preventDefault();
    this.dragActive.set(false);
    if (event.dataTransfer?.files?.length) {
      const droppedFiles = Array.from(event.dataTransfer.files);
      this.value = [...(this.value ?? []), ...droppedFiles];
      this.onTouched();
    }
  }

  onDragLeave(event: DragEvent): void {
    event.preventDefault();
    this.dragActive.set(false);
  }

  // -----------------------------
  // Utility
  // -----------------------------
  getImageUrl(file: File): string {
    return URL.createObjectURL(file);
  }

  ngOnDestroy(): void {
    this.stateChanges.complete();
  }

  @HostBinding('class.disabled') get isDisabled() {
    return this.disabled;
  }
}
