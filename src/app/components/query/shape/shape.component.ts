import { Component, Input, Output, EventEmitter } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';

@Component({
  selector: 'app-query-shape',
  standalone: true,
  imports: [FormsModule, MatFormFieldModule, MatInputModule],
  templateUrl: `./shape.component.html`,
  styleUrl: './shape.component.scss',
})
export class ShapeComponent {
  @Input() length: number | null = null;
  @Output() lengthChange = new EventEmitter<number | null>();

  @Input() width: number | null = null;
  @Output() widthChange = new EventEmitter<number | null>();
}
