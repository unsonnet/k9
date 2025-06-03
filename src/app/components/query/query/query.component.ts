import { Component } from '@angular/core';
import { MaterialComponent } from '../material/material.component';
import { ShapeComponent } from '../shape/shape.component';
import { ImagesComponent } from '../images/images.component';
import { MatButtonModule } from '@angular/material/button';
import { Query } from '../../../models/query.model';

@Component({
  selector: 'app-query',
  standalone: true,
  imports: [
    MaterialComponent,
    ShapeComponent,
    ImagesComponent,
    MatButtonModule,
  ],
  templateUrl: './query.component.html',
  styleUrl: './query.component.scss',
})
export class QueryComponent {
  selectedMaterial: string | null = null;
  length: number | null = null;
  width: number | null = null;
  uploadedImages: { name: string; url: string; file: File }[] = [];

  isMaterialInvalid = false;
  isImagesInvalid = false;

  onSearch(): void {
    this.isMaterialInvalid = !this.selectedMaterial;
    this.isImagesInvalid = this.uploadedImages.length === 0;

    if (this.isMaterialInvalid || this.isImagesInvalid) return;

    const query: Query = {
      type: 'tile',
      material: this.selectedMaterial!,
      length: this.length,
      width: this.width,
      images: this.uploadedImages.map((img) => img.file),
    };

    console.log('Search Query:', query);
    alert('Search initiated. Check console for details.');
  }

  // ⬇ called in template on input changes
  onMaterialChange(value: string | null): void {
    this.selectedMaterial = value;
    this.isMaterialInvalid = false;
  }

  onImagesChange(images: { name: string; url: string; file: File }[]): void {
    this.uploadedImages = images;
    this.isImagesInvalid = false;
  }
}