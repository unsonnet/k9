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

  onSearch(): void {
    if (!this.selectedMaterial) {
      alert('Must select material');
      return;
    }
    const images = this.uploadedImages.map((img) => img.file);
    if (images.length == 0) {
      alert('Must upload at least one image');
      return;
    }

    const query: Query = {
      type: 'tile',
      material: this.selectedMaterial,
      length: this.length,
      width: this.width,
      images: images,
    };

    console.log('Search Query:', query);
    alert('Search initiated. Check console for details.');
  }
}
