import { Component, Input, Output, EventEmitter } from '@angular/core';
import { MatListModule } from '@angular/material/list';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';

@Component({
  selector: 'app-query-images',
  standalone: true,
  imports: [MatListModule, MatIconModule, MatButtonModule],
  templateUrl: `./images.component.html`,
  styleUrl: './images.component.scss',
})
export class ImagesComponent {
  @Input() images!: { name: string; url: string; file: File }[];
  @Output() imagesChange = new EventEmitter<typeof this.images>();

  isDragOver = false;

  onDragOver(event: DragEvent): void {
    event.preventDefault();
    this.isDragOver = true;
  }

  onDragLeave(event: DragEvent): void {
    event.preventDefault();
    this.isDragOver = false;
  }

  onDrop(event: DragEvent): void {
    event.preventDefault();
    this.isDragOver = false;
    if (event.dataTransfer?.files) this.handleFiles(event.dataTransfer.files);
  }

  onSelect(event: Event): void {
    const target = event.target as HTMLInputElement;
    if (target.files) this.handleFiles(target.files);
  }

  handleFiles(fileList: FileList): void {
    const newImages = Array.from(fileList)
      .filter((file) => file.type.startsWith('image/'))
      .map((file) => {
        const reader = new FileReader();
        const promise = new Promise<{ name: string; url: string; file: File }>(
          (resolve) => {
            reader.onload = () => {
              resolve({ name: file.name, url: reader.result as string, file });
            };
          },
        );
        reader.readAsDataURL(file);
        return promise;
      });

    Promise.all(newImages).then((results) => {
      this.images = [...this.images, ...results];
      this.imagesChange.emit(this.images);
    });
  }

  remove(index: number): void {
    this.images.splice(index, 1);
    this.imagesChange.emit(this.images);
  }
}
