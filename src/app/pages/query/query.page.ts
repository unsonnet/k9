import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatButtonModule } from '@angular/material/button';
import { MatListModule } from '@angular/material/list';
import { MatIconModule } from '@angular/material/icon';

@Component({
  selector: 'app-query',
  imports: [
    FormsModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatButtonModule,
    MatListModule,
    MatIconModule,
  ],
  templateUrl: './query.page.html',
  styleUrls: ['./query.page.scss'],
})
export class QueryPage {
  materials: string[] = ['Wood', 'Steel', 'Plastic', 'Glass'];
  selectedMaterial: string | null = null;

  length: number | null = null;
  width: number | null = null;

  isDragOver = false;
  uploadedImages: { name: string; url: string; file: File }[] = [];

  // Drag and Drop Events
  onDragOver(event: DragEvent): void {
    event.preventDefault();
    this.isDragOver = true;
  }

  onDragLeave(event: DragEvent): void {
    event.preventDefault();
    this.isDragOver = false;
  }

  onFileDrop(event: DragEvent): void {
    event.preventDefault();
    this.isDragOver = false;

    if (event.dataTransfer?.files) {
      this.handleFiles(event.dataTransfer.files);
    }
  }

  onFileSelect(event: Event): void {
    const target = event.target as HTMLInputElement;
    if (target.files) {
      this.handleFiles(target.files);
    }
  }

  handleFiles(files: FileList): void {
    Array.from(files).forEach((file) => {
      if (file.type.startsWith('image/')) {
        const reader = new FileReader();
        reader.onload = () => {
          this.uploadedImages.push({
            name: file.name,
            url: reader.result as string,
            file: file,
          });
        };
        reader.readAsDataURL(file);
      }
    });
  }

  removeImage(index: number): void {
    this.uploadedImages.splice(index, 1);
  }

  onSearch(): void {
    const query = {
      type: 'tile',
      material: this.selectedMaterial,
      length: this.length,
      width: this.width,
      images: this.uploadedImages.map((img) => img.file),
    };

    console.log('Search Query:', query);

    // Replace this with actual search logic or emit to a parent component
    alert('Search initiated. Check console for details.');
  }
}
