import { Component, input } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-product-thumbnails',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './thumbnails.html',
  styleUrl: './thumbnails.scss',
})
export class ProductThumbnailsComponent {
  readonly imageUrls = input.required<string[]>();
  readonly selectedIndex = input.required<number>();
  readonly select = input.required<(i: number) => void>();
}
