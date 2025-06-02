// src/app/product-cell/product-cell.component.ts
import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Product } from '../../../models/product.model';
import { FormsModule } from '@angular/forms'; // Needed for [(ngModel)]

@Component({
  selector: 'app-product-cell',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './cell.component.html',
  styleUrl: './cell.component.scss',
})
export class ProductCellComponent {
  @Input() product!: Product;
  @Output() productClick = new EventEmitter<Product>();

  selected = false;

  handleClick() {
    this.productClick.emit(this.product);
  }
}
