import { Component } from '@angular/core';
import { MaterialComponent } from '../../components/query/material/material.component';
import { ShapeComponent } from '../../components/query/shape/shape.component';
import { ImagesComponent } from '../../components/query/images/images.component';
import { MatButtonModule } from '@angular/material/button';

@Component({
  selector: 'app-query',
  standalone: true,
  imports: [
    MaterialComponent,
    ShapeComponent,
    ImagesComponent,
    MatButtonModule,
  ],
  templateUrl: './query.page.html',
  styleUrls: ['./query.page.scss'],
})
export class QueryPage {
  selectedMaterial: string | null = null;
  length: number | null = null;
  width: number | null = null;
  uploadedImages: { name: string; url: string; file: File }[] = [];

  onSearch(): void {
    const query = {
      type: 'tile',
      material: this.selectedMaterial,
      length: this.length,
      width: this.width,
      images: this.uploadedImages.map((img) => img.file),
    };

    console.log('Search Query:', query);
    alert('Search initiated. Check console for details.');
  }
}
