import { Component, Input, Output, EventEmitter } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatSelectModule } from '@angular/material/select';

@Component({
  selector: 'app-query-material',
  standalone: true,
  imports: [FormsModule, MatFormFieldModule, MatSelectModule],
  templateUrl: `./material.component.html`,
  styleUrl: './material.component.scss',
})
export class MaterialComponent {
  @Input() materials: string[] = ['Wood', 'Steel', 'Plastic', 'Glass'];

  @Input() value: string | null = null;
  @Output() valueChange = new EventEmitter<string | null>();
}
